import json
import unittest
from fastapi.testclient import TestClient
from src.final_assesment.main import app

class TestWorkflowRoutes(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

    def test_create_workflow_success_and_invalid(self):
        valid_payload = {
            "name": "Text Pipeline",
            "description": "Simple text upper pipeline",
            "steps": [
                {
                    "name": "To Upper",
                    "type": "TRANSFORM_TEXT",
                    "config": {
                        "operation": "uppercase",
                        "input_key": "raw",
                        "output_key": "clean"
                    }
                }
            ]
        }
        res = self.client.post("/workflows", json=valid_payload)
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["name"], "Text Pipeline")
        self.assertIn("id", body["data"])

        invalid_payload = {
            "name": "   ",
            "steps": []
        }
        res_invalid = self.client.post("/workflows", json=invalid_payload)
        self.assertIn(res_invalid.status_code, [400, 422])
        self.assertFalse(res_invalid.json()["success"])

    def test_list_and_get_workflow(self):
        create_res = self.client.post("/workflows", json={"name": "Fetch WF", "steps": []})
        wf_id = create_res.json()["data"]["id"]

        list_res = self.client.get("/workflows")
        self.assertEqual(list_res.status_code, 200)
        self.assertTrue(list_res.json()["success"])
        self.assertIsInstance(list_res.json()["data"], list)

        get_res = self.client.get(f"/workflows/{wf_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertTrue(get_res.json()["success"])
        self.assertEqual(get_res.json()["data"]["id"], wf_id)

        not_found = self.client.get("/workflows/999999")
        self.assertEqual(not_found.status_code, 404)
        self.assertFalse(not_found.json()["success"])
        self.assertEqual(not_found.json()["error"], "Workflow not found")

    def test_order_processing_example_sequential_execution(self):
        order_workflow = {
            "name": "Order Processing",
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
        res = self.client.post("/workflows", json=order_workflow)
        wf_id = res.json()["data"]["id"]

        input_data = {
            "customer_name": "poku",
            "unit_price": 200,
            "quantity": 5,
            "discount": 100,
            "email": "POKU"
        }
        exec_res = self.client.post(f"/workflows/{wf_id}/execute", json={"input": input_data})
        self.assertEqual(exec_res.status_code, 200)
        body = exec_res.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertEqual(data["status"], "success")

        output = json.loads(data["output"])
        self.assertEqual(output["customer_name"], "poku")
        self.assertEqual(output["unit_price"], 200)
        self.assertEqual(output["quantity"], 5)
        self.assertEqual(output["discount"], 100)
        self.assertEqual(output["email"], "POKU")
        self.assertEqual(output["normalized_name"], "POKU")
        self.assertEqual(output["total_price"], 1000)
        self.assertEqual(output["final_price"], 900)
        self.assertEqual(output["normalized_email"], "poku")
        self.assertEqual(len(data["step_results"]), 4)

    def test_generate_workflow_from_natural_language(self):
        desc = "Convert customer name to uppercase, calculate total price by multiplying unit price and quantity, subtract discount, and convert email to lowercase."
        res = self.client.post("/workflows/generate", json={"description": desc})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertIn("name", data)
        self.assertIn("steps", data)
        self.assertGreaterEqual(len(data["steps"]), 4)

    def test_generate_workflow_invalid(self):
        res = self.client.post("/workflows/generate", json={"description": "   "})
        self.assertIn(res.status_code, [400, 422])
        self.assertFalse(res.json()["success"])

    def test_execute_workflow_not_found(self):
        res = self.client.post("/workflows/999999/execute", json={"input": {}})
        self.assertEqual(res.status_code, 404)
        self.assertFalse(res.json()["success"])
        self.assertEqual(res.json()["error"], "Workflow not found")

    def test_failed_execution_recording(self):
        wf = {
            "name": "Zero Div WF",
            "steps": [
                {
                    "name": "Div Zero",
                    "type": "CALCULATE",
                    "config": {
                        "operation": "divide",
                        "left_key": "val",
                        "right_key": "zero",
                        "output_key": "out"
                    }
                }
            ]
        }
        wf_res = self.client.post("/workflows", json=wf)
        wf_id = wf_res.json()["data"]["id"]

        exec_res = self.client.post(f"/workflows/{wf_id}/execute", json={"input": {"val": 10, "zero": 0}})
        self.assertEqual(exec_res.status_code, 200)
        body = exec_res.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertEqual(data["status"], "failed")
        self.assertIn("Division by zero", data["error"])

    def test_execution_history_and_single_lookup(self):
        wf_res = self.client.post("/workflows", json={"name": "History WF", "steps": []})
        wf_id = wf_res.json()["data"]["id"]

        e1 = self.client.post(f"/workflows/{wf_id}/execute", json={"input": {"n": 1}}).json()["data"]
        e2 = self.client.post(f"/workflows/{wf_id}/execute", json={"input": {"n": 2}}).json()["data"]

        history_res = self.client.get(f"/workflows/{wf_id}/executions")
        self.assertEqual(history_res.status_code, 200)
        self.assertTrue(history_res.json()["success"])
        history = history_res.json()["data"]
        self.assertGreaterEqual(len(history), 2)
        ids = [item["id"] for item in history]
        self.assertIn(e1["id"], ids)
        self.assertIn(e2["id"], ids)

        single_res = self.client.get(f"/executions/{e1['id']}")
        self.assertEqual(single_res.status_code, 200)
        self.assertTrue(single_res.json()["success"])
        self.assertEqual(single_res.json()["data"]["id"], e1["id"])

        not_found_res = self.client.get("/executions/999999")
        self.assertEqual(not_found_res.status_code, 404)
        self.assertFalse(not_found_res.json()["success"])

    def test_successful_and_invalid_retry(self):
        wf = {
            "name": "Retryable WF",
            "steps": [
                {
                    "name": "Div Step",
                    "type": "CALCULATE",
                    "config": {
                        "operation": "divide",
                        "left_key": "num",
                        "right_key": "denom",
                        "output_key": "res"
                    }
                }
            ]
        }
        wf_res = self.client.post("/workflows", json=wf)
        wf_id = wf_res.json()["data"]["id"]

        failed_res = self.client.post(f"/workflows/{wf_id}/execute", json={"input": {"num": 10, "denom": 0}})
        failed_id = failed_res.json()["data"]["id"]
        self.assertEqual(failed_res.json()["data"]["status"], "failed")

        retry_res = self.client.post(f"/executions/{failed_id}/retry")
        self.assertEqual(retry_res.status_code, 200)
        self.assertTrue(retry_res.json()["success"])
        retry_data = retry_res.json()["data"]
        self.assertNotEqual(retry_data["id"], failed_id)
        self.assertEqual(retry_data["workflow_id"], wf_id)
        self.assertEqual(retry_data["retry_count"], 1)

        orig_check = self.client.get(f"/executions/{failed_id}")
        self.assertEqual(orig_check.status_code, 200)
        self.assertEqual(orig_check.json()["data"]["status"], "failed")

        success_wf = self.client.post("/workflows", json={"name": "Success Only", "steps": []})
        s_id = success_wf.json()["data"]["id"]
        s_exec = self.client.post(f"/workflows/{s_id}/execute", json={"input": {}}).json()["data"]

        bad_retry = self.client.post(f"/executions/{s_exec['id']}/retry")
        self.assertEqual(bad_retry.status_code, 400)
        self.assertFalse(bad_retry.json()["success"])
        self.assertIn("Only failed executions can be retried", bad_retry.json()["error"])

    def test_global_error_handling(self):
        res = self.client.post("/workflows", json={"name": "", "steps": "not_a_list"})
        self.assertIn(res.status_code, [400, 422])
        self.assertFalse(res.json()["success"])
        self.assertIn("error", res.json())

if __name__ == "__main__":
    unittest.main()
