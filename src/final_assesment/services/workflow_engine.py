import json
from src.final_assesment.services.ai_service import classify_text_with_ai

def run_transform_text(config: dict, context: dict):
    input_key = config.get("input_key")
    output_key = config.get("output_key")
    operation = str(config.get("operation", "")).lower()

    if not input_key:
        raise KeyError("Step missing input_key")
    if input_key not in context:
        raise KeyError(f"Missing input key: {input_key}")
    if not output_key:
        raise KeyError("Step missing output_key")

    text_value = str(context[input_key])

    if operation in ["uppercase", "upper", "upppercase"]:
        result = text_value.upper()
    elif operation in ["lowercase", "lower"]:
        result = text_value.lower()
    elif operation in ["strip", "trim"]:
        result = text_value.strip()
    else:
        raise ValueError(f"Unsupported operation: {operation}")

    context[output_key] = result
    return result

def run_calculate(config: dict, context: dict):
    left_key = config.get("left_key")
    right_key = config.get("right_key")
    output_key = config.get("output_key")
    operation = str(config.get("operation", "")).lower()

    if not left_key:
        raise KeyError("Step missing left_key")
    if left_key not in context:
        raise KeyError(f"Missing left key: {left_key}")
    if not right_key:
        raise KeyError("Step missing right_key")
    if right_key not in context:
        raise KeyError(f"Missing right key: {right_key}")
    if not output_key:
        raise KeyError("Step missing output_key")

    try:
        left_val = float(context[left_key])
        right_val = float(context[right_key])
    except (ValueError, TypeError):
        raise ValueError("Invalid numeric value for calculation")

    if operation in ["add", "plus", "+"]:
        result = left_val + right_val
    elif operation in ["subtract", "minus", "sub", "-"]:
        result = left_val - right_val
    elif operation in ["multiply", "mul", "*"]:
        result = left_val * right_val
    elif operation in ["divide", "div", "/"]:
        if right_val == 0:
            raise ZeroDivisionError("Division by zero")
        result = left_val / right_val
    else:
        raise ValueError(f"Unsupported operation: {operation}")

    if result.is_integer():
        result = int(result)

    context[output_key] = result
    return result

def run_ai_classify(config: dict, context: dict):
    input_key = config.get("input_key")
    output_key = config.get("output_key")
    categories = config.get("categories")

    if not input_key:
        raise KeyError("Step missing input_key")
    if input_key not in context:
        raise KeyError(f"Missing input key: {input_key}")
    if not output_key:
        raise KeyError("Step missing output_key")

    text_value = str(context[input_key])
    result = classify_text_with_ai(text_value, categories)
    context[output_key] = result
    return result

def run_single_step(step: dict, context: dict):
    step_type = str(step.get("type", "")).upper()
    config = step.get("config", {})
    if not isinstance(config, dict):
        config = {}

    if step_type in ["TRANSFORM_TEXT", "TEXT_TRANSFORM", "TRANSFORM"]:
        return run_transform_text(config, context)
    elif step_type in ["CALCULATE", "ARITHMETIC", "ARITHMATIC"]:
        return run_calculate(config, context)
    elif step_type in ["AI_CLASSIFY", "CLASSIFY", "CLASSIFICATION"]:
        return run_ai_classify(config, context)
    else:
        raise ValueError(f"Unsupported step type: {step_type}")

def execute_steps(steps: list, initial_input):
    context = {}
    if isinstance(initial_input, dict):
        if "input" in initial_input and isinstance(initial_input["input"], dict):
            context.update(initial_input["input"])
        else:
            context.update(initial_input)
    elif isinstance(initial_input, str):
        try:
            parsed = json.loads(initial_input)
            if isinstance(parsed, dict):
                if "input" in parsed and isinstance(parsed["input"], dict):
                    context.update(parsed["input"])
                else:
                    context.update(parsed)
            else:
                context["input"] = parsed
        except Exception:
            context["input"] = initial_input
    elif initial_input is not None:
        context["input"] = initial_input

    step_results = []
    status = "success"
    error = None

    for index, step in enumerate(steps):
        step_name = step.get("name", f"Step {index + 1}")
        step_type = step.get("type", "")

        try:
            val = run_single_step(step, context)
            step_results.append({
                "name": step_name,
                "type": step_type,
                "status": "success",
                "output": val
            })
        except Exception as e:
            status = "failed"
            error = str(e)
            step_results.append({
                "name": step_name,
                "type": step_type,
                "status": "failed",
                "error": str(e)
            })
            break

    return status, context, step_results, error
