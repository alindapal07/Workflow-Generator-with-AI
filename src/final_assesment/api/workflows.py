import json
from fastapi import APIRouter, Depends
from src.final_assesment.schemas.workflow import WorkflowCreate, ExecuteRequest, GenerateRequest
from src.final_assesment.services.workflow_engine import execute_steps
from src.final_assesment.services.ai_service import generate_workflow_from_natural_language
from src.final_assesment.core.responses import success_response
from src.final_assesment.core.dependencies import get_workflow_repository
from src.final_assesment.repository.workflow_repository import WorkflowRepository
from src.final_assesment.error.exceptions import WorkflowNotFoundException, InvalidWorkflowInputException

router = APIRouter()

@router.post("/workflows", status_code=201)
async def create_workflow(body: WorkflowCreate, repo: WorkflowRepository = Depends(get_workflow_repository)):
    if not body.name or not body.name.strip():
        raise InvalidWorkflowInputException("Workflow name cannot be empty")

    wf = await repo.create_workflow(
        name=body.name.strip(),
        description=body.description,
        steps=body.steps
    )
    return success_response(
        data={
            "id": wf.id,
            "name": wf.name,
            "description": wf.description,
            "steps": wf.steps,
            "created_at": wf.created_at.isoformat()
        },
        message="Workflow created successfully",
        status_code=201
    )

@router.get("/workflows")
async def list_workflows(repo: WorkflowRepository = Depends(get_workflow_repository)):
    workflows = await repo.list_workflows()
    data = [
        {
            "id": wf.id,
            "name": wf.name,
            "description": wf.description,
            "steps": wf.steps,
            "created_at": wf.created_at.isoformat()
        }
        for wf in workflows
    ]
    return success_response(data=data, message="Workflows retrieved successfully")

@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: int, repo: WorkflowRepository = Depends(get_workflow_repository)):
    wf = await repo.get_workflow(workflow_id)
    if not wf:
        raise WorkflowNotFoundException("Workflow not found")
    return success_response(
        data={
            "id": wf.id,
            "name": wf.name,
            "description": wf.description,
            "steps": wf.steps,
            "created_at": wf.created_at.isoformat()
        },
        message="Workflow retrieved successfully"
    )

@router.post("/workflows/generate")
async def generate_workflow(body: GenerateRequest):
    if not body.description or not body.description.strip():
        raise InvalidWorkflowInputException("Workflow description cannot be empty")
    data = generate_workflow_from_natural_language(body.description)
    return success_response(data=data, message="Workflow definition generated successfully")

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: int, body: ExecuteRequest = None, repo: WorkflowRepository = Depends(get_workflow_repository)):
    wf = await repo.get_workflow(workflow_id)
    if not wf:
        raise WorkflowNotFoundException("Workflow not found")

    input_payload = {}
    if body:
        if body.input is not None:
            input_payload = body.input
        else:
            raw_data = body.model_dump()
            raw_data.pop("input", None)
            input_payload = raw_data

    input_str = json.dumps(input_payload) if isinstance(input_payload, (dict, list)) else str(input_payload)

    status, context, step_results, error = execute_steps(wf.steps, input_payload)

    execution = await repo.create_execution(
        workflow_id=wf.id,
        status=status,
        input_data=input_str,
        output_data=json.dumps(context) if status == "success" else None,
        error=error,
        retry_count=0,
        step_results=step_results
    )
    return success_response(
        data={
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status,
            "input": execution.input,
            "output": execution.output,
            "error": execution.error,
            "retry_count": execution.retry_count,
            "step_results": execution.step_results,
            "created_at": execution.created_at.isoformat(),
            "finished_at": execution.finished_at.isoformat() if execution.finished_at else None
        },
        message="Workflow executed successfully"
    )

@router.get("/workflows/{workflow_id}/executions")
async def get_workflow_executions(workflow_id: int, repo: WorkflowRepository = Depends(get_workflow_repository)):
    wf = await repo.get_workflow(workflow_id)
    if not wf:
        raise WorkflowNotFoundException("Workflow not found")

    executions = await repo.list_executions(workflow_id)
    data = [
        {
            "id": ex.id,
            "workflow_id": ex.workflow_id,
            "status": ex.status,
            "input": ex.input,
            "output": ex.output,
            "error": ex.error,
            "retry_count": ex.retry_count,
            "step_results": ex.step_results,
            "created_at": ex.created_at.isoformat(),
            "finished_at": ex.finished_at.isoformat() if ex.finished_at else None
        }
        for ex in executions
    ]
    return success_response(data=data, message="Executions retrieved successfully")
