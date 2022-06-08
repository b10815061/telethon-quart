from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column, Integer, String, MetaData,String

SQLALCHEMY_DATABASE_URL = "postgresql://tommy:0000@localhost:5432/telegram"

engine = create_engine(SQLALCHEMY_DATABASE_URL,echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


metadata = MetaData()
users = Table('channels', metadata,
    Column('user_id', String),
    Column('priority', Integer),
    Column('channel_id', String),
    Column('message',String),
)

metadata.create_all(engine)

##print("success")

Base = declarative_base() # inherit from this class to create ORM models

