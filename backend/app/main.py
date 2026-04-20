from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.formulas import router as formula_router
from .api.herbs import router as herb_router
from .api.recognitions import router as recognition_router
from .api.statistics import router as statistics_router
from .core.config import settings
from .core.responses import register_exception_handlers
from .db.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(herb_router)
app.include_router(formula_router)
app.include_router(statistics_router)
app.include_router(recognition_router)


@app.get("/", tags=["system"])
def read_root():
    return {
        "message": "TCM Visual Query System API is running.",
        "database": settings.mysql_database,
    }


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}
