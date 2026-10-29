import json
from fastapi import APIRouter, Depends
from src.final_assesment.services.workflow_engine import execute_steps
from src.final_assesment.core.responses import success_response
from src.final_assesment.core.dependencies import get_workflow_repository
from src.final_assesment.repository.workflow_repository import WorkflowRepository
from src.final_assesment.error.exceptions import (
    ExecutionNotFoundException,
    WorkflowNotFoundException,
    InvalidWorkflowInputException
)

router = APIRouter()

@router.get("/executions/{execution_id}")
async def get_execution(execution_id: int, repo: WorkflowRepository = Depends(get_workflow_repository)):
    execution = await repo.get_execution(execution_id)
    if not execution:
        raise ExecutionNotFoundException("Execution not found")
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
        message="Execution retrieved successfully"
    )

@router.post("/executions/{execution_id}/retry")
async def retry_execution(execution_id: int, repo: WorkflowRepository = Depends(get_workflow_repository)):
    execution = await repo.get_execution(execution_id)
    if not execution:
        raise ExecutionNotFoundException("Execution not found")

    if execution.status != "failed":
        raise InvalidWorkflowInputException("Only failed executions can be retried")

    wf = await repo.get_workflow(execution.workflow_id)
    if not wf:
        raise WorkflowNotFoundException("Workflow not found")

    try:
        input_data = json.loads(execution.input)
    except Exception:
        input_data = execution.input

    status, context, step_results, error = execute_steps(wf.steps, input_data)

    new_execution = await repo.create_execution(
        workflow_id=wf.id,
        status=status,
        input_data=execution.input,
        output_data=json.dumps(context) if status == "success" else None,
        error=error,
        retry_count=execution.retry_count + 1,
        step_results=step_results
    )
    return success_response(
        data={
            "id": new_execution.id,
            "workflow_id": new_execution.workflow_id,
            "status": new_execution.status,
            "input": new_execution.input,
            "output": new_execution.output,
            "error": new_execution.error,
            "retry_count": new_execution.retry_count,
            "step_results": new_execution.step_results,
            "created_at": new_execution.created_at.isoformat(),
            "finished_at": new_execution.finished_at.isoformat() if new_execution.finished_at else None
        },
        message="Execution retried successfully"
    )
