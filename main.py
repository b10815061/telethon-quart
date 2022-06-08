from quart import Quart,render_template
from quart import websocket
from util import utils
import asyncio
import json
import DB
import get_dialog
import base64
from telethon.sync import TelegramClient, events

app = Quart(__name__)
api_id = 12655046
api_hash = 'd84ab8008abfb3ec244630d2a6778fc6'
client = None

@app.route('/')
async def hello():
    return await render_template('index.html')

@app.websocket('/conn')
async def conn():
    while True:
        phone = await websocket.receive()
        global client
        client = TelegramClient(phone,api_id,api_hash)
        await client.connect()
        ### login part
        if not await client.is_user_authorized():
            try:
                await client.send_code_request(phone)
                await websocket.send("System : please Enter Code to Enter")
                Code = await websocket.receive()
                await client.sign_in(phone,Code)
            except:
                await websocket.send("System : Invalid Phone Number")
                await websocket.send("System : Login aborted")
                return
        await websocket.send('System : Connected')

        ### initial database
        await get_dialog.get(client)
        ### send images
        me = await client.get_me()
        chan = await get_dialog.retrive_all(me.id)
        for c in chan :
            print(c.channel_id)
            chat_id = c.channel_id
            pri = await get_dialog.retrive_prior(me.id,chat_id)
            try:
                with open(f'./images/{c.channel_id}.png','rb')as f:
                        image_data = f.read()
                        b64 = base64.b64encode(image_data).decode()
                        
                        try:
                            user_name = (await client.get_entity(int(chat_id))).title
                            print(user_name)
                            pri = await get_dialog.retrive_prior(me.id,chat_id)

                        except:
                            U = await client.get_entity(int(chat_id))
                            user_name = utils.name2str(U.first_name) + " " + utils.name2str(U.last_name)
                            print(f'cannot get {chat_id}')
                        image = {
                            "tag" :"image",
                            "b64" : b64,
                            "id"  : chat_id,
                            "name" : user_name,
                            "pri" :pri
                        }
                        await websocket.send(str(image))
                        print(f'{c.channel_id} sent')
            except:
                try:
                    user_name = (await client.get_entity(int(chat_id))).title
                    print(user_name)
                    pri = await get_dialog.retrive_prior(me.id,chat_id)

                except:
                    U = await client.get_entity(int(chat_id))
                    user_name = utils.name2str(U.first_name) + " " + utils.name2str(U.last_name)
                image = {
                            "tag" :"image",
                            "b64" : "None",
                            "id"  : chat_id,
                            "name" : user_name,
                            "pri" :pri
                        }
                await websocket.send(str(image))
            print("DONE SENDING IMAGE")
        ### hook on message
        @client.on(events.NewMessage())
        async def handler(event):
            channel_id = await event.get_chat()
            print(event)
            
            try:
                name = channel_id.title
            except:
                name = channel_id.id
            try:
                sender = await event.get_sender()
                if sender.username != None:
                    sender = sender.username
                else:
                    lname = sender.last_name if sender.last_name!=None else ""
                    sender = sender.first_name + lname
            except:
                sender = channel_id.title
            
            data = event.message.message
            obj = {
                'channel' : name,
                'from'    : sender,
                'message' : data
            }
            await websocket.send(str(obj))

        await client.run_until_disconnected()

@app.websocket('/pri')
async def pri():
    while True:
        data = await websocket.receive()
        if client!=None and client.is_connected():
            pri_pair = json.loads(data)
            print(pri_pair["channel"] , pri_pair["pri"])
            await get_dialog.set_pri(pri_pair["channel"],pri_pair["pri"])
            await websocket.send(f'System : set priority of {pri_pair["channel"]} to {pri_pair["pri"]}')
        else:
           await websocket.send("System : You are not Connected!")


@app.websocket('/ws')
async def ws():
    while True:
        data = await websocket.receive()
        if client!=None and client.is_connected():
            pair = json.loads(data)
            try : 
                await client.send_message(pair["channel"],pair["message"])
                await websocket.send(f'{pair["channel"]} : {pair["message"]}')
            except : 
                try:
                    id = pair["channel"]
                    name = await client.get_entity(int(id))
                    print(name)
                    await client.send_message(entity=name,message=pair["message"])
                    await websocket.send(f'{pair["channel"]} : {pair["message"]}')
                except:
                    await websocket.send(f'you can\'t write in this channel ({pair["channel"]})')
        else:
           await websocket.send("System : You are not Connected!")

@app.websocket('/disconnect')
async def disconnect():
    while True:
        dis = await websocket.receive()
        print("disconnect!")
        await client.disconnect()
        await websocket.send("System : Disconnected")

if __name__ == "__main__":
    asyncio.run(app.run_task())