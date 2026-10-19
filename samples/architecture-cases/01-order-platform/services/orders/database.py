from sqlmodel import SQLModel, Session, create_engine
DATABASE_URL = 'postgresql://demo:demo@orders-db:5432/orders'
engine = create_engine(DATABASE_URL)
def session():
    return Session(engine)
