from sqlalchemy import select
from dbconfig import engine
from sqlalchemy.orm import Session
from model import channels

async def get_pri():
    conn = engine.connect()
    s = select(channels).where(channels.user_id == "1")
    res = conn.execute(s)
    for row in res:
        print(row)