from sqlmodel import SQLModel, Session, create_engine
DATABASE_URL = 'postgresql://demo:demo@fulfillment-db:5432/fulfillment'
engine = create_engine(DATABASE_URL)
def session():
    return Session(engine)
