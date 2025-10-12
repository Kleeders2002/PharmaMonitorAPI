from sqlmodel import SQLModel, create_engine

DATABASE_URL = "postgresql://postgres:kleeders2002@localhost/PharmaMonitorDB"
engine = create_engine(DATABASE_URL)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    from sqlmodel import Session
    with Session(engine) as session:
        yield session