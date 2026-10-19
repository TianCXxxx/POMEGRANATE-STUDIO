from sqlmodel import SQLModel, Session, create_engine
DATABASE_URL = 'postgresql://demo:demo@tracking-db:5432/tracking'
engine = create_engine(DATABASE_URL)
def session():
    return Session(engine)
