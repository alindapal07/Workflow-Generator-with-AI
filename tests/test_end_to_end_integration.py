import json
import unittest
from fastapi.testclient import TestClient
from src.final_assesment.main import app

class TestEndToEndWorkflowIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_end_to_end_order_processing_full_flow(self):
        order_workflow = {
            "name": "Order Processing E2E",
            "description": "Calculates order totals and normalizes customer data",
            "steps": [
                {
                    "name": "Normalize Customer Name",
                    "type": "TRANSFORM_TEXT",
                    "config": {
                        "operation": "uppercase",
                        "input_key": "customer_name",
                        "output_key": "normalized_name"
                    }
                },
                {
                    "name": "Calculate Total Price",
                    "type": "CALCULATE",
                    "config": {
                        "operation": "multiply",
                        "left_key": "unit_price",
                        "right_key": "quantity",
                        "output_key": "total_price"
                    }
                },
                {
                    "name": "Apply Discount",
                    "type": "CALCULATE",
                    "config": {
                        "operation": "subtract",
                        "left_key": "total_price",
                        "right_key": "discount",
                        "output_key": "final_price"
                    }
                },
                {
                    "name": "Normalize Email",
                    "type": "TRANSFORM_TEXT",
                    "config": {
                        "operation": "lowercase",
                        "input_key": "email",
                        "output_key": "normalized_email"
                    }
                }
            ]
        }
        create_res = self.client.post("/workflows", json=order_workflow)
        self.assertEqual(create_res.status_code, 201)
        create_data = create_res.json()
        self.assertTrue(create_data["success"])
        wf_id = create_data["data"]["id"]
        self.assertIsInstance(wf_id, int)

        order_input = {
            "customer_name": "poku",
            "unit_price": 200,
            "quantity": 5,
            "discount": 100,
            "email": "POKU"
        }
        exec_res = self.client.post(f"/workflows/{wf_id}/execute", json={"input": order_input})
        self.assertEqual(exec_res.status_code, 200)
        exec_body = exec_res.json()
        self.assertTrue(exec_body["success"])
        exec_data = exec_body["data"]
        self.assertEqual(exec_data["status"], "success")
        self.assertIsNone(exec_data["error"])
        self.assertEqual(exec_data["retry_count"], 0)

        output = json.loads(exec_data["output"])
        self.assertEqual(output["customer_name"], "poku")
        self.assertEqual(output["unit_price"], 200)
        self.assertEqual(output["quantity"], 5)
        self.assertEqual(output["discount"], 100)
        self.assertEqual(output["email"], "POKU")
        self.assertEqual(output["normalized_name"], "POKU")
        self.assertEqual(output["total_price"], 1000)
        self.assertEqual(output["final_price"], 900)
        self.assertEqual(output["normalized_email"], "poku")

        self.assertEqual(len(exec_data["step_results"]), 4)
        for step in exec_data["step_results"]:
            self.assertEqual(step["status"], "success")

        exec_id = exec_data["id"]
        get_exec_res = self.client.get(f"/executions/{exec_id}")
        self.assertEqual(get_exec_res.status_code, 200)
        single_data = get_exec_res.json()["data"]
        self.assertEqual(single_data["id"], exec_id)
        self.assertEqual(single_data["status"], "success")

        history_res = self.client.get(f"/workflows/{wf_id}/executions")
        self.assertEqual(history_res.status_code, 200)
        history_list = history_res.json()["data"]
        self.assertGreaterEqual(len(history_list), 1)
        history_ids = [item["id"] for item in history_list]
        self.assertIn(exec_id, history_ids)

    def test_end_to_end_natural_language_to_execution(self):
        nl_prompt = "Convert customer name to uppercase, calculate total price by multiplying unit price and quantity, subtract discount, and convert email to lowercase."
        gen_res = self.client.post("/workflows/generate", json={"description": nl_prompt})
        self.assertEqual(gen_res.status_code, 200)
        gen_body = gen_res.json()
        self.assertTrue(gen_body["success"])
        generated_wf = gen_body["data"]
        self.assertIn("name", generated_wf)
        self.assertIn("steps", generated_wf)
        self.assertGreaterEqual(len(generated_wf["steps"]), 4)

        create_res = self.client.post("/workflows", json=generated_wf)
        self.assertEqual(create_res.status_code, 201)
        wf_id = create_res.json()["data"]["id"]

        exec_input = {
            "customer_name": "jane doe",
            "unit_price": 50,
            "quantity": 4,
            "discount": 20,
            "email": "JANE@EXAMPLE.COM"
        }
        exec_res = self.client.post(f"/workflows/{wf_id}/execute", json={"input": exec_input})
        self.assertEqual(exec_res.status_code, 200)
        exec_data = exec_res.json()["data"]
        self.assertEqual(exec_data["status"], "success")
        output = json.loads(exec_data["output"])
        self.assertEqual(output["normalized_name"], "JANE DOE")
        self.assertEqual(output["total_price"], 200)
        self.assertEqual(output["final_price"], 180)
        self.assertEqual(output["normalized_email"], "jane@example.com")

    def test_end_to_end_ai_classification_pipeline(self):
        pipeline = {
            "name": "Customer Support Pipeline",
            "steps": [
                {
                    "name": "Normalize Name",
                    "type": "TRANSFORM_TEXT",
                    "config": {
                        "operation": "uppercase",
                        "input_key": "name",
                        "output_key": "clean_name"
                    }
                },
                {
                    "name": "Classify Sentiment",
                    "type": "AI_CLASSIFY",
                    "config": {
                        "input_key": "feedback",
                        "output_key": "sentiment",
                        "categories": ["positive", "negative", "neutral"]
                    }
                },
                {
                    "name": "Compute Score",
                    "type": "CALCULATE",
                    "config": {
                        "operation": "multiply",
                        "left_key": "rating",
                        "right_key": "weight",
                        "output_key": "weighted_score"
                    }
                }
            ]
        }
        create_res = self.client.post("/workflows", json=pipeline)
        wf_id = create_res.json()["data"]["id"]

        exec_res = self.client.post(
            f"/workflows/{wf_id}/execute",
            json={"input": {"name": "sam", "feedback": "Great service and awesome quality!", "rating": 5, "weight": 2}}
        )
        self.assertEqual(exec_res.status_code, 200)
        exec_data = exec_res.json()["data"]
        self.assertEqual(exec_data["status"], "success")
        output = json.loads(exec_data["output"])
        self.assertEqual(output["clean_name"], "SAM")
        self.assertEqual(output["sentiment"], "positive")
        self.assertEqual(output["weighted_score"], 10)

    def test_end_to_end_failure_and_retry_lifecycle(self):
        calc_wf = {
            "name": "Division Workflow",
            "steps": [
                {
                    "name": "Divide Numbers",
                    "type": "CALCULATE",
                    "config": {
                        "operation": "divide",
                        "left_key": "num",
                        "right_key": "denom",
                        "output_key": "result"
                    }
                }
            ]
        }
        wf_res = self.client.post("/workflows", json=calc_wf)
        wf_id = wf_res.json()["data"]["id"]

        failed_res = self.client.post(f"/workflows/{wf_id}/execute", json={"input": {"num": 100, "denom": 0}})
        self.assertEqual(failed_res.status_code, 200)
        failed_data = failed_res.json()["data"]
        self.assertEqual(failed_data["status"], "failed")
        self.assertIn("Division by zero", failed_data["error"])
        failed_id = failed_data["id"]

        retry_res = self.client.post(f"/executions/{failed_id}/retry")
        self.assertEqual(retry_res.status_code, 200)
        retry_data = retry_res.json()["data"]
        self.assertNotEqual(retry_data["id"], failed_id)
        self.assertEqual(retry_data["workflow_id"], wf_id)
        self.assertEqual(retry_data["retry_count"], 1)

        original_check = self.client.get(f"/executions/{failed_id}")
        self.assertEqual(original_check.status_code, 200)
        self.assertEqual(original_check.json()["data"]["status"], "failed")

        success_wf = self.client.post("/workflows", json={"name": "No Failure WF", "steps": []})
        succ_id = success_wf.json()["data"]["id"]
        succ_exec = self.client.post(f"/workflows/{succ_id}/execute", json={"input": {}}).json()["data"]

        invalid_retry = self.client.post(f"/executions/{succ_exec['id']}/retry")
        self.assertEqual(invalid_retry.status_code, 400)
        self.assertFalse(invalid_retry.json()["success"])
        self.assertIn("Only failed executions can be retried", invalid_retry.json()["error"])

    def test_end_to_end_direct_payload_and_error_handling(self):
        wf = {
            "name": "Direct Input WF",
            "steps": [
                {
                    "name": "Strip Name",
                    "type": "TRANSFORM_TEXT",
                    "config": {
                        "operation": "strip",
                        "input_key": "user",
                        "output_key": "clean_user"
                    }
                }
            ]
        }
        create_res = self.client.post("/workflows", json=wf)
        wf_id = create_res.json()["data"]["id"]

        direct_res = self.client.post(f"/workflows/{wf_id}/execute", json={"user": "   charlie   "})
        self.assertEqual(direct_res.status_code, 200)
        output = json.loads(direct_res.json()["data"]["output"])
        self.assertEqual(output["clean_user"], "charlie")

        bad_wf = self.client.get("/workflows/999999")
        self.assertEqual(bad_wf.status_code, 404)
        self.assertFalse(bad_wf.json()["success"])

        bad_exec = self.client.get("/executions/999999")
        self.assertEqual(bad_exec.status_code, 404)
        self.assertFalse(bad_exec.json()["success"])

        empty_name_wf = self.client.post("/workflows", json={"name": "   ", "steps": []})
        self.assertEqual(empty_name_wf.status_code, 400)
        self.assertFalse(empty_name_wf.json()["success"])

        empty_gen = self.client.post("/workflows/generate", json={"description": "   "})
        self.assertEqual(empty_gen.status_code, 400)
        self.assertFalse(empty_gen.json()["success"])

if __name__ == "__main__":
    unittest.main()
