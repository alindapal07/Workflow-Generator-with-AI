import unittest
from src.final_assesment.services.workflow_engine import execute_steps

class TestWorkflowEngine(unittest.TestCase):
    def test_text_transformations(self):
        steps = [
            {
                "name": "Upper",
                "type": "TRANSFORM_TEXT",
                "config": {
                    "operation": "uppercase",
                    "input_key": "raw_name",
                    "output_key": "upper_name"
                }
            },
            {
                "name": "Lower",
                "type": "TRANSFORM_TEXT",
                "config": {
                    "operation": "lowercase",
                    "input_key": "raw_email",
                    "output_key": "lower_email"
                }
            },
            {
                "name": "Strip",
                "type": "TRANSFORM_TEXT",
                "config": {
                    "operation": "strip",
                    "input_key": "raw_text",
                    "output_key": "clean_text"
                }
            }
        ]
        input_data = {
            "raw_name": "alice",
            "raw_email": "ALICE@EXAMPLE.COM",
            "raw_text": "   spaced string   "
        }
        status, context, results, error = execute_steps(steps, input_data)
        self.assertEqual(status, "success")
        self.assertIsNone(error)
        self.assertEqual(context["upper_name"], "ALICE")
        self.assertEqual(context["lower_email"], "alice@example.com")
        self.assertEqual(context["clean_text"], "spaced string")

    def test_arithmetic_calculations(self):
        steps = [
            {
                "name": "Add",
                "type": "CALCULATE",
                "config": {
                    "operation": "add",
                    "left_key": "n1",
                    "right_key": "n2",
                    "output_key": "add_res"
                }
            },
            {
                "name": "Sub",
                "type": "CALCULATE",
                "config": {
                    "operation": "subtract",
                    "left_key": "n1",
                    "right_key": "n2",
                    "output_key": "sub_res"
                }
            },
            {
                "name": "Mul",
                "type": "CALCULATE",
                "config": {
                    "operation": "multiply",
                    "left_key": "n1",
                    "right_key": "n2",
                    "output_key": "mul_res"
                }
            },
            {
                "name": "Div",
                "type": "CALCULATE",
                "config": {
                    "operation": "divide",
                    "left_key": "n1",
                    "right_key": "n2",
                    "output_key": "div_res"
                }
            }
        ]
        input_data = {"n1": 20, "n2": 4}
        status, context, results, error = execute_steps(steps, input_data)
        self.assertEqual(status, "success")
        self.assertEqual(context["add_res"], 24)
        self.assertEqual(context["sub_res"], 16)
        self.assertEqual(context["mul_res"], 80)
        self.assertEqual(context["div_res"], 5)

    def test_sequential_step_execution_and_context_passing(self):
        steps = [
            {
                "name": "Step 1",
                "type": "CALCULATE",
                "config": {
                    "operation": "multiply",
                    "left_key": "price",
                    "right_key": "qty",
                    "output_key": "total"
                }
            },
            {
                "name": "Step 2",
                "type": "CALCULATE",
                "config": {
                    "operation": "subtract",
                    "left_key": "total",
                    "right_key": "discount",
                    "output_key": "final_amount"
                }
            }
        ]
        input_data = {"price": 100, "qty": 3, "discount": 50}
        status, context, results, error = execute_steps(steps, input_data)
        self.assertEqual(status, "success")
        self.assertEqual(context["total"], 300)
        self.assertEqual(context["final_amount"], 250)
        self.assertEqual(len(results), 2)

    def test_ai_text_classification_step(self):
        steps = [
            {
                "name": "Classify Feedback",
                "type": "AI_CLASSIFY",
                "config": {
                    "input_key": "comment",
                    "output_key": "sentiment",
                    "categories": ["positive", "negative", "neutral"]
                }
            }
        ]
        input_data = {"comment": "This product is awesome and great!"}
        status, context, results, error = execute_steps(steps, input_data)
        self.assertEqual(status, "success")
        self.assertEqual(context["sentiment"], "positive")

    def test_missing_input_fields(self):
        steps = [
            {
                "name": "Step Missing",
                "type": "TRANSFORM_TEXT",
                "config": {
                    "operation": "uppercase",
                    "input_key": "unknown_key",
                    "output_key": "out"
                }
            }
        ]
        status, context, results, error = execute_steps(steps, {"other_key": "val"})
        self.assertEqual(status, "failed")
        self.assertIn("unknown_key", error)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "failed")

    def test_division_by_zero(self):
        steps = [
            {
                "name": "Divide Zero",
                "type": "CALCULATE",
                "config": {
                    "operation": "divide",
                    "left_key": "numerator",
                    "right_key": "denominator",
                    "output_key": "out"
                }
            }
        ]
        status, context, results, error = execute_steps(steps, {"numerator": 50, "denominator": 0})
        self.assertEqual(status, "failed")
        self.assertIn("Division by zero", error)

    def test_unsupported_operation_and_type(self):
        steps = [
            {
                "name": "Invalid Op",
                "type": "CALCULATE",
                "config": {
                    "operation": "modulo",
                    "left_key": "a",
                    "right_key": "b",
                    "output_key": "out"
                }
            }
        ]
        status, context, results, error = execute_steps(steps, {"a": 10, "b": 3})
        self.assertEqual(status, "failed")
        self.assertIn("Unsupported operation", error)

if __name__ == "__main__":
    unittest.main()
