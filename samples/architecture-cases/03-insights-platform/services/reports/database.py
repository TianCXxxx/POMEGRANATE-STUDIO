from sqlmodel import SQLModel, Session, create_engine
DATABASE_URL = 'postgresql://demo:demo@reports-db:5432/reports'
engine = create_engine(DATABASE_URL)
def session():
    return Session(engine)
