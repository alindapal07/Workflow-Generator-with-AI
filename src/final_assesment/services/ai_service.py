import os
import json

def classify_text_with_ai(text: str, categories: list = None):
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0)
            options = categories if categories else ["positive", "negative", "neutral"]
            prompt = f"Classify this text into one category from {options}. Return ONLY the category name in lowercase.\nText: {text}"
            res = llm.invoke(prompt)
            result = str(res.content).strip().lower()
            for opt in options:
                if opt.lower() in result:
                    return opt.lower()
            return result
        except Exception:
            pass

    lower_text = text.lower()
    if categories:
        for cat in categories:
            if cat.lower() in lower_text:
                return cat.lower()
        return categories[0].lower()

    negative_keywords = ["bad", "terrible", "poor", "hate", "awful", "negative", "angry", "worst", "down", "bug"]
    positive_keywords = ["good", "great", "excellent", "love", "awesome", "positive", "happy", "best"]

    for word in negative_keywords:
        if word in lower_text:
            return "negative"
    for word in positive_keywords:
        if word in lower_text:
            return "positive"
    return "neutral"

def generate_workflow_from_natural_language(description: str):
    if not description or not description.strip():
        raise ValueError("Workflow description cannot be empty")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, temperature=0)
            prompt = (
                "You are an expert workflow generator. Convert the user's description into a structured JSON workflow.\n"
                "Allowed step types are TRANSFORM_TEXT, CALCULATE, and AI_CLASSIFY.\n"
                "TRANSFORM_TEXT config: operation (uppercase, lowercase, strip), input_key, output_key.\n"
                "CALCULATE config: operation (add, subtract, multiply, divide), left_key, right_key, output_key.\n"
                "AI_CLASSIFY config: input_key, output_key, categories (optional list).\n"
                "Return ONLY a valid JSON object with keys 'name' (string) and 'steps' (list).\n"
                f"Description: {description}"
            )
            res = llm.invoke(prompt)
            content = str(res.content).strip()
            if content.startswith("```"):
                content = content.strip("`")
                if content.startswith("json"):
                    content = content[4:].strip()
            data = json.loads(content)
            if isinstance(data, dict) and "name" in data and "steps" in data:
                return data
        except Exception:
            pass

    lower = description.lower()
    steps = []

    if "uppercase" in lower or "customer" in lower:
        steps.append({
            "name": "Normalize Customer Name",
            "type": "TRANSFORM_TEXT",
            "config": {
                "operation": "uppercase",
                "input_key": "customer_name",
                "output_key": "normalized_name"
            }
        })

    if "multiply" in lower or "total price" in lower:
        steps.append({
            "name": "Calculate Total Price",
            "type": "CALCULATE",
            "config": {
                "operation": "multiply",
                "left_key": "unit_price",
                "right_key": "quantity",
                "output_key": "total_price"
            }
        })

    if "discount" in lower or "subtract" in lower:
        steps.append({
            "name": "Apply Discount",
            "type": "CALCULATE",
            "config": {
                "operation": "subtract",
                "left_key": "total_price",
                "right_key": "discount",
                "output_key": "final_price"
            }
        })

    if "lowercase" in lower or "email" in lower:
        steps.append({
            "name": "Normalize Email",
            "type": "TRANSFORM_TEXT",
            "config": {
                "operation": "lowercase",
                "input_key": "email",
                "output_key": "normalized_email"
            }
        })

    if "classify" in lower or "sentiment" in lower:
        steps.append({
            "name": "Classify Sentiment",
            "type": "AI_CLASSIFY",
            "config": {
                "input_key": "feedback",
                "output_key": "sentiment"
            }
        })

    if not steps:
        steps.append({
            "name": "Default Step",
            "type": "TRANSFORM_TEXT",
            "config": {
                "operation": "strip",
                "input_key": "input_text",
                "output_key": "output_text"
            }
        })

    return {
        "name": "Generated Workflow",
        "steps": steps
    }

