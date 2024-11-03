from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

# Defines the SQLite database URL for connecting to the local database file 'database.db'.
sqlite_url = "sqlite:///database.db"

# Specifies connection arguments for SQLite, allowing usage in a multithreaded environment.
connect_args = {"check_same_thread": False}

# Creates a database engine using the specified SQLite URL and connection arguments.
engine = create_engine(sqlite_url, connect_args=connect_args)

# Creates the database tables using SQLModel's metadata and the provided engine.
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Provides a database session to be used with dependency injection in FastAPI routes.
def get_session():
    with Session(engine) as session:
        yield session

# Defines a dependency for obtaining a database session, used for type hinting with FastAPI.
SessionDep = Annotated[Session, Depends(get_session)]
