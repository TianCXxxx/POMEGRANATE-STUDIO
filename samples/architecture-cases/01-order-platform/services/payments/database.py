from sqlmodel import SQLModel, Session, create_engine
DATABASE_URL = 'postgresql://demo:demo@payment-db:5432/payments'
engine = create_engine(DATABASE_URL)
def session():
    return Session(engine)
