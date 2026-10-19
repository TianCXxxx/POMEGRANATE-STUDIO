from sqlmodel import SQLModel, Session, create_engine
DATABASE_URL = 'postgresql://demo:demo@carrier-db:5432/carrier'
engine = create_engine(DATABASE_URL)
def session():
    return Session(engine)
