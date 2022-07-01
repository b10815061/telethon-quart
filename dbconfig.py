from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column, Integer, String, MetaData, String

SQLALCHEMY_DATABASE_URL = "postgresql://tommy:0000@localhost:5432/telegram"

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


metadata = MetaData()
users = Table('channels', metadata,
              Column('user_id', String),
              Column('priority', Integer, unique=True),
              Column('channel_id', String),
              Column('message', String)
              )

setting = Table('setting', metadata,
                Column('user_id', String),
                Column('font_size', Integer),
                Column('language', String)
                )

metadata.create_all(engine)

# print("success")

Base = declarative_base()  # inherit from this class to create ORM models
