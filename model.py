from sqlalchemy import Column, Integer, String, PrimaryKeyConstraint

from dbconfig import Base


class channels(Base):
    __tablename__ = "channels"  # table name in the database
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'channel_id'),
    )

    user_id = Column(String)
    channel_id = Column(String)
    priority = Column(Integer)
    message = Column(String)


class setting(Base):
    __tablename__ = "setting"
    __table_args__ = (PrimaryKeyConstraint('user_id'),)

    user_id = Column(String)
    font_size = Column(Integer)
    language = Column(String)
