from contextlib import asynccontextmanager
from fastapi import FastAPI
from alembic import command
from alembic.config import Config
from src.final_assesment.api.workflows import router as workflows_router
from src.final_assesment.api.executions import router as executions_router
from src.final_assesment.core.responses import success_response
from src.final_assesment.error.handlers import register_error_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    yield

app = FastAPI(
    title="Workflow Automation Backend",
    version="1.0.0",
    lifespan=lifespan
)

register_error_handlers(app)

app.include_router(workflows_router)
app.include_router(executions_router)

@app.get("/health")
async def get_health():
    return success_response(message="All set, proceed !")

