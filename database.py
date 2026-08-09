from sqlmodel import SQLModel, create_engine, Session

# This creates a local file called "tracefix.db" — that's your whole database
DATABASE_URL = "sqlite:///tracefix.db"

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session