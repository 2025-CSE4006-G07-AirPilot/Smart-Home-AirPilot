# app/core/db.py에 DB 엔진과 세션 관련 코드를 둡니다.

from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    from app.models.room import Room
    from app.models.edge import Edge
    from app.models.device import Device
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
