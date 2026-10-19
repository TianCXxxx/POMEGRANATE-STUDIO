from sqlmodel import SQLModel, Session, create_engine
DATABASE_URL = 'postgresql://demo:demo@catalog-db:5432/catalog'
engine = create_engine(DATABASE_URL)
def session():
    return Session(engine)
