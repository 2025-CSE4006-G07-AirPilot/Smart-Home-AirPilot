from contextlib import asynccontextmanager
from fastapi import FastAPI

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
