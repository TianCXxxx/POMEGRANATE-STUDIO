from sqlmodel import SQLModel, Session, create_engine
DATABASE_URL = 'postgresql://demo:demo@metrics-db:5432/metrics'
engine = create_engine(DATABASE_URL)
def session():
    return Session(engine)
