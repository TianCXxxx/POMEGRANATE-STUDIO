from sqlmodel import SQLModel, Session, create_engine
DATABASE_URL = 'postgresql://demo:demo@warehouse-db:5432/warehouse'
engine = create_engine(DATABASE_URL)
def session():
    return Session(engine)
