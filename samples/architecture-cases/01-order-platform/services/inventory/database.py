from sqlmodel import SQLModel, Session, create_engine
DATABASE_URL = 'postgresql://demo:demo@inventory-db:5432/inventory'
engine = create_engine(DATABASE_URL)
def session():
    return Session(engine)
