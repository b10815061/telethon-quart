from sqlalchemy.orm import Session
from sqlalchemy import select
import model
from model import channels
from dbconfig import engine
import telethon
from PIL import Image
import shutil

size = 64,64

async def get(client):
    me = await client.get_me()
    print(me)
    dialogs = await client.get_dialogs()
    for i in range(10):
       
        if(type(dialogs[i].message.peer_id)==telethon.tl.types.PeerChannel):
            #print(dialogs[i].message.peer_id)
            #emit('dialog',dialogs)
            await insert_user_channel(me.id,dialogs[i].message.peer_id.channel_id,i)
            try:
                im = Image.open(f'./images/{dialogs[i].message.peer_id.channel_id}.png')
            except:
                print("not found" + f'./images/{dialogs[i].message.peer_id.channel_id}.png')
                await client.download_profile_photo(dialogs[i],file=f'{dialogs[i].message.peer_id.channel_id}.png',download_big=False)
                try:
                    shutil.move(f'{dialogs[i].message.peer_id.channel_id}.png',f'./images/{dialogs[i].message.peer_id.channel_id}.png')
                    im = Image.open(f'./images/{dialogs[i].message.peer_id.channel_id}.png')
                    im.thumbnail(size,Image.ANTIALIAS)
                    im.save(f'./images/{dialogs[i].message.peer_id.channel_id}.png','PNG')
                except:
                    print("file not found")
        elif(type(dialogs[i].message.peer_id)==telethon.tl.types.PeerChat):
            #print(dialogs[i].message.peer_id)
            await insert_user_channel(me.id,dialogs[i].message.peer_id.chat_id,i)
            try:
                im = Image.open(f'./images/{dialogs[i].message.peer_id.chat_id}.png')
            except:
                print("not found" + f'./images/{dialogs[i].message.peer_id.chat_id}.png')
                await client.download_profile_photo(dialogs[i],file=f'{dialogs[i].message.peer_id.chat_id}.png',download_big=False)
                try:
                    shutil.move(f'{dialogs[i].message.peer_id.chat_id}.png',f'./images/{dialogs[i].message.peer_id.chat_id}.png')
                    im = Image.open(f'./images/{dialogs[i].message.peer_id.chat_id}.png')
                    im.thumbnail(size,Image.ANTIALIAS)
                    im.save(f'./images/{dialogs[i].message.peer_id.chat_id}.png','PNG')
                except:
                    print("file not found")
        else:
            #print(dialogs[i].message.peer_id)
            #print(dialogs[i].message.peer_id.user_id)
            await insert_user_channel(me.id,dialogs[i].message.peer_id.user_id,i)
            try:
                im = Image.open(f'./images/{dialogs[i].message.peer_id.user_id}.png')
            except:
                print("not found" + f'./images/{dialogs[i].message.peer_id.user_id}.png')
                await client.download_profile_photo(dialogs[i],file=f'{dialogs[i].message.peer_id.user_id}.png',download_big=False)
                try:
                    shutil.move(f'{dialogs[i].message.peer_id.user_id}.png',f'./images/{dialogs[i].message.peer_id.user_id}.png')
                    im = Image.open(f'./images/{dialogs[i].message.peer_id.user_id}.png')
                    im.thumbnail(size,Image.ANTIALIAS)
                    im.save(f'./images/{dialogs[i].message.peer_id.user_id}.png','PNG')
                except:
                    print("file not found")
            
        #messages = await client.get_messages(dialogs[i].id,limit=400)
        #for message in messages:
            #print(message.message)
            #print("\n")
    
async def insert_user_channel(client_id,input_channel,input_pri):
    ### find if it exists
    with Session(engine) as session:
        exist = session.query(channels)\
        .filter(channels.user_id==str(client_id))\
        .filter(channels.channel_id==str(input_channel))\
        .all()
        
        if(len(exist)<1):
            
            star_channel = model.channels(user_id=str(client_id),priority=input_pri,channel_id=str(input_channel),message="")
            session.add(star_channel)
            session.commit()
            return
        
        
        #for row in exist:   
            #print(row.user_id, end=" ")
            #print(row.channel_id, end=" ")
            #print(row.priority)
        
        #print("\n")

async def retrive_prior(client_id,input_channel):
    ### find if it exists
    with Session(engine) as session:
        channel = session.query(channels)\
        .filter(channels.user_id==str(client_id))\
        .filter(channels.channel_id==str(input_channel))\
        .first()
    
    return (channel.priority)

async def retrive_all(client_id):
    ### find if it exists
    with Session(engine) as session:
        channel = session.query(channels)\
        .filter(channels.user_id==str(client_id))\
        .order_by(channels.priority.asc())\
        .all()
    
    return (channel)

async def set_pri(channel_id,pri):
    with Session(engine) as session:
        channel = session.query(channels)\
        .filter(channels.channel_id==str(channel_id))\
        .update({'priority':int(pri)})

        session.commit()
    return
        
        