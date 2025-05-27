from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from backend.config.config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
db_session = scoped_session(sessionmaker(autocommit=False,
                                       autoflush=False,
                                       bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # Import all modules here that might define models
    from backend.app.models import User, HealthRecord, Appointment
Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    init_db()
