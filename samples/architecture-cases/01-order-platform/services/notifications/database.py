from sqlmodel import SQLModel, Session, create_engine
DATABASE_URL = 'postgresql://demo:demo@notify-db:5432/notifications'
engine = create_engine(DATABASE_URL)
def session():
    return Session(engine)
