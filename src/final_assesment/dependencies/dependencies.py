from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.final_assesment.db.session import SessionLocal
from src.final_assesment.core.config import get_settings, Settings
from src.final_assesment.repository.workflow_repository import WorkflowRepository

async def get_db():
    async with SessionLocal() as session:
        yield session

def get_workflow_repository(db: AsyncSession = Depends(get_db)) -> WorkflowRepository:
    return WorkflowRepository(db)

def get_app_settings() -> Settings:
    return get_settings()

