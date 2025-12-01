from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.edge_ai.routers.nlp import router as edge_nlp_router
from app.edge_ai.routers.control import router as edge_control_router

from app.core.db import init_db
from app.routers import rooms, edges, devices


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup 시점
    init_db()
    yield
    # shutdown 시점에 정리할 게 있으면 여기서 처리


app = FastAPI(lifespan=lifespan)

app.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
app.include_router(edges.router, prefix="/edges", tags=["edges"])
app.include_router(devices.router, prefix="/devices", tags=["devices"])

app.include_router(edge_nlp_router)
app.include_router(edge_control_router)


@app.get("/health")
def health():
    return {"status": "ok"}