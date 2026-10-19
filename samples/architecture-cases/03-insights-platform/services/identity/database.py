from sqlmodel import SQLModel, Session, create_engine
DATABASE_URL = 'postgresql://demo:demo@identity-db:5432/identity'
engine = create_engine(DATABASE_URL)
def session():
    return Session(engine)
