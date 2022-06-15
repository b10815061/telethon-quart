from re import A
import time 
from quart import Quart,render_template,request
from quart import websocket
from util import utils
import asyncio
import json
import DB
import get_dialog
import base64
from telethon.sync import TelegramClient, events
import telethon

app = Quart(__name__)
api_id = 12655046
api_hash = 'd84ab8008abfb3ec244630d2a6778fc6'
client = None

@app.route('/')
async def hello():
    return await render_template('index.html')

@app.route('/getMessage') ## endPoint http://localhost:5000/getMessage?channel=(arbitrary)
async def getMessage():
    if client!=None and client.is_connected():
        channel_id = request.args.get("channel")
        from_message_id = 0 if request.args.get("message_id") == 0 else int(request.args.get("message_id"))
        print(from_message_id)
        try:
            channel_instance = await client.get_entity((int(channel_id)))
            msgs = await client.get_messages(channel_instance,limit=20,offset_id=from_message_id)
            context = []
            for msg_instance in msgs:
                ## get the sender of the msg
                try :
                    ### !!! messages in Chat (2 frineds channel) has no from_id attribute
                    if(msg_instance.from_id!=None):
                        sender_instance = await client.get_entity(msg_instance.from_id.user_id)
                    else:
                        ## which menas if the from_id is NoneType, then the channel itself is a user
                        sender_instance = channel_instance
                    if sender_instance.username!=None: 
                        sender = sender_instance.username
                    elif sender_instance.first_name!=None :
                        lname = sender_instance.last_name if sender_instance.last_name!=None else ""
                        sender = sender_instance.first_name + lname
                    else :
                        sender = sender_instance.title
                except Exception as e:
                    print(e)
                    print(channel_instance)
                    print(msgs[0])
                ## get the message content
                try : 
                    msg_content = msg_instance.message  ## need to consider photo, videos here (not considered yet)
                    msg_content.replace("\"","\\\"")    ## to address the quote in msg
                except Exception as e : 
                    print(e)
                    print(msg_instance)
                    print(msg_content)
                ## get the time message has sent
                msg_time = msg_instance.date

                obj = {
                    "tag"       : "message",
                    "channel"   : channel_id,
                    "from"      : sender,
                    "data"      : msg_content,
                    "message_id": msg_instance.id, ## save the message id for advanced functions
                    "timestamp" : str(msg_time)
                }
                print(msg_content,end="\n\n\n")
                context.append(obj)
            
            message ={
                "code":200,
                "context" : context
            }
        except Exception as e :
            print(e)
            message = {"code":500,"error":"channel not found"}
            print("channel_not_found")
    else:
        message = {"code":400,"error":"System : You are not connected"}
    return message


@app.websocket('/conn')
async def conn():
    while True:
        phone = await websocket.receive()
        global client
        client = TelegramClient('+886918622947',api_id,api_hash)
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
        sys = {
            "tag" : "system",
            "context" : "Connected"
        }

        sys = str(sys).replace("\'","\"")
        await websocket.send(sys)

        ## searching PoS
        async for message in client.iter_messages('testing', search='vava'):
            continue
            #print(message.id,message)

        ## get the unread counts while user is offline
        dia = await client.get_dialogs()
        x = []
        for d in dia:
            if(type(d.message.peer_id)==telethon.tl.types.PeerChannel):
                x.append([d.unread_count,d.message.peer_id.channel_id])
            elif(type(d.message.peer_id)==telethon.tl.types.PeerChat):
                x.append([d.unread_count,d.message.peer_id.chat_id])
            else:
                x.append([d.unread_count,d.message.peer_id.user_id])

        for e in x:
            unread ={
                "tag" : "initial",
                "channel" : e[1],
                "count"  : e[0]
            }
            unread = str(unread).replace("\'","\"")
            await websocket.send(unread)

        ### initial database
        await get_dialog.get(client)
        ### send images
        me = await client.get_me()
        channels = await get_dialog.retrive_all(me.id)
        # for c in channels :
        #     chat_id = c.channel_id
        #     pri = await get_dialog.retrive_prior(me.id,chat_id)
        #     try:
        #         with open(f'./images/{c.channel_id}.png','rb')as f:
        #                 image_data = f.read()
        #                 b64 = base64.b64encode(image_data).decode()
        #                 try:
        #                     user_name = (await client.get_entity(int(chat_id))).title
        #                     pri = await get_dialog.retrive_prior(me.id,chat_id)
        #                 except:
        #                     U = await client.get_entity(int(chat_id))
        #                     user_name = utils.name2str(U.first_name) + " " + utils.name2str(U.last_name)
        #                     #print(f'cannot get {chat_id}')
        #                 image = {
        #                     "tag" :"profile",
        #                     "b64" : b64,
        #                     "id"  : chat_id,
        #                     "name" : user_name,
        #                     "pri" :pri
        #                 }
        #                 await websocket.send(str(image))
        #                 #print(f'{c.channel_id} sent')
        #     except:
        #         try:
        #             user_name = (await client.get_entity(int(chat_id))).title
        #             pri = await get_dialog.retrive_prior(me.id,chat_id)

        #         except:
        #             U = await client.get_entity(int(chat_id))
        #             user_name = utils.name2str(U.first_name) + " " + utils.name2str(U.last_name)
        #         image = {
        #                     "tag" :"image",
        #                     "b64" : "None",
        #                     "id"  : chat_id,
        #                     "name" : user_name,
        #                     "pri" :pri
        #                 }
        #         await websocket.send(str(image))
        # print("DONE SENDING IMAGE\n\n")

        ### hook on the incoming messages
        @client.on(events.NewMessage())
        async def handler(event):
                
            channel = await event.get_chat()
            '''print(channel,end="\n\n\n\n")
            print(event.message,end="\n\n\n")'''

            channel_id = channel.id
            try:
                sender = await event.get_sender()
                if sender.username != None:
                    sender = sender.username
                elif sender.first_name!=None:
                    lname = sender.last_name if sender.last_name!=None else ""
                    sender = sender.first_name + lname
                else:
                    sender = sender.title
            except: ## for those channels containing anonymous users
                sender = channel.title
            
            time_stamp = event.message.date
            if type(event.message.media) == telethon.tl.types.MessageMediaPhoto :
                print(event.message.media)
                photo_byte = (event.message.media.photo.file_reference)
                ## convert byte to base64 here
                data = base64.b64encode(photo_byte).decode()
                tag = "image"
            else : 
                data = event.message.message
                print(type(data))
                data = data.replace("\\","\\\\")
                data = data.replace("\"","\\\"")
                print(data)
                tag = "message"
            print(data,end="\n\n\n")
            obj = {
                "tag"     : tag,
                "channel" : channel_id,
                "from"    : sender,
                "data"    : data,
                "time_stamp" : str(time_stamp)
            }
            print(obj,end="\n\n")
            obj = str(obj)
            obj = obj.replace("\\\'","\'")
            obj = obj.replace(", '", ', "').replace("',", '",')
            obj = obj.replace(": '", ': "').replace("':", '":')
            obj = obj.replace("{'", '{"').replace("'}", '"}')
            obj = obj.replace("\\\\","\\")
            print(obj,end="\n\n")
            #obj = str(obj).replace("\'","\"") ## 'data' : 'didn't' -> "data" : "didn"t" (this is for JSON format)
            await websocket.send(obj)
            '''try:
                await client.send_read_acknowledge(channel_id.id,event.message)
            except:
                await client.send_read_acknowledge(channel_id.title,event.message)'''

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