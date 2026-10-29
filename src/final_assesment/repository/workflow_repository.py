from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.final_assesment.models.workflow import Workflow, Execution

class WorkflowRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_workflow(self, name: str, description: str | None, steps: list) -> Workflow:
        wf = Workflow(
            name=name,
            description=description,
            steps=steps
        )
        self.db.add(wf)
        await self.db.commit()
        await self.db.refresh(wf)
        return wf

    async def list_workflows(self) -> list[Workflow]:
        result = await self.db.execute(select(Workflow).order_by(Workflow.id.desc()))
        return list(result.scalars().all())

    async def get_workflow(self, workflow_id: int) -> Workflow | None:
        return await self.db.get(Workflow, workflow_id)

    async def create_execution(
        self,
        workflow_id: int,
        status: str,
        input_data: str,
        output_data: str | None,
        error: str | None,
        retry_count: int,
        step_results: list
    ) -> Execution:
        execution = Execution(
            workflow_id=workflow_id,
            status=status,
            input=input_data,
            output=output_data,
            error=error,
            retry_count=retry_count,
            step_results=step_results,
            finished_at=datetime.now(timezone.utc)
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        return execution

    async def get_execution(self, execution_id: int) -> Execution | None:
        return await self.db.get(Execution, execution_id)

    async def list_executions(self, workflow_id: int) -> list[Execution]:
        result = await self.db.execute(
            select(Execution).filter(Execution.workflow_id == workflow_id).order_by(Execution.id.desc())
        )
        return list(result.scalars().all())

