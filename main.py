from email.message import Message
import os
from sqlite3 import Timestamp
import time
from typing import Any, NewType
from quart import Quart, render_template, request
from quart import websocket
from util import utils
import asyncio
import json
import DB
import get_dialog
import base64
from telethon.sync import TelegramClient, events
import telethon
import pyrlottie
import nest_asyncio


nest_asyncio.apply()

app = Quart(__name__)
api_id = 12655046
api_hash = 'd84ab8008abfb3ec244630d2a6778fc6'
client_list: dict[int, TelegramClient] = dict()

# !!!!too slow


async def sendGIF(cur: int, path: str) -> str:
    print("entering lock")
    # pylottie.convertLottie2GIF(path,f'{cur}.gif') ## the implementation here uses asyncio, which is incompatible with quart(also uses asyncio), includes nest_asyncio to support it.
    await pyrlottie.convSingleLottie(lottieFile=pyrlottie.LottieFile(path), destFiles=[f'{cur}.gif'])
    # send byte index to frontend
    # address slow convertion prob here with queue.
    with open(f'{cur}.gif', 'rb') as file:
        gif_data = file.read()
        data = base64.b64encode(gif_data).decode()
    os.remove(f'{cur}.gif')
    os.remove(path)
    print("out of lock")
    return data


@app.route('/')
async def hello():
    return await render_template('index.html')

MessageObject = NewType('MessageObject', object)


@app.route('/client_list')
async def list():
    global client_list
    res = ""
    for item in client_list:
        print(item)
        res += str(item)
        print(client_list[item])
    return res


@app.route('/test')
async def test():
    userID = int(request.args.get("user_id"))

    global client_list
    if (userID) in client_list:
        print(f"{userID} in list")
        print(client_list[userID])
    test = await client_list[userID].get_me()
    print(test)
    return str(test.id) + "," + str(test.is_self)

# endPoint http://localhost:5000/getMessage?channel=(arbitrary)


@app.route('/getMessage')
async def getMessage():
    user = int(request.args.get("user_id"))
    global client_list
    key = utils.find_client(user, client_list)
    if key != -1:
        client = client_list[key]
        if client.is_connected():
            channel_id: int = request.args.get("channel")
            from_message_id: int = 0 if request.args.get(
                "message_id") == 0 else int(request.args.get("message_id"))
            try:
                channel_instance: telethon.Channel = await client.get_entity((int(channel_id)))
                msgs: list[telethon.message] = await client.get_messages(channel_instance, limit=5, offset_id=from_message_id)
                context: list[MessageObject] = []

                msg_instance: telethon.message
                for msg_instance in msgs:
                    # get the sender of the msg
                    try:
                        # !!! messages in Chat (2 frineds channel) has no from_id attribute
                        if(msg_instance.from_id != None):
                            sender_instance = await client.get_entity(msg_instance.from_id.user_id)
                        else:
                            # which menas if the from_id is NoneType, then the channel itself is a user
                            sender_instance = channel_instance
                        try:
                            if sender_instance.username != None:
                                sender = sender_instance.username
                            elif sender_instance.first_name != None:
                                lname = sender_instance.last_name if sender_instance.last_name != None else ""
                                sender = sender_instance.first_name + lname
                            else:
                                print("AN ERROR MIGHT OCCUR")
                                print(sender_instance, end="\n\n\n")
                        except:
                            sender = sender_instance.title
                    except Exception as e:
                        print(e)
                        print(channel_instance)
                        print(msgs[0])
                    # get the message content
                    try:
                        if type(msg_instance.media) == telethon.tl.types.MessageMediaPhoto:
                            tag = "image"
                            image_path = await client.download_media(msg_instance)
                            with open(image_path, 'rb') as f:
                                image_data = f.read()
                                msg_content = base64.b64encode(
                                    image_data).decode()
                            os.remove(image_path)
                        elif type(msg_instance.media) == telethon.tl.types.MessageMediaDocument:
                            # the rcv data is a mp4 (gif on the telegram perspective)
                            if(msg_instance.media.document.mime_type == "video/mp4"):
                                tag = "mp4"
                                sticker_path = await client.download_media(msg_instance)
                                with open(sticker_path, 'rb') as file:
                                    mp4_data = file.read()
                                    # convert mp4 into b64
                                    msg_content = base64.b64encode(
                                        mp4_data).decode()
                                os.remove(sticker_path)
                            # its a telegram sticker (.tgs file)
                            elif(msg_instance.media.document.mime_type == "application/x-tgsticker"):
                                tag = "gif"
                                # use the library to convert .tgs to .gif; The frontend will need to specific the gif extension in tag
                                sticker_path = await client.download_media(msg_instance)
                                # convert .tgs to .gif
                                cur = time.time_ns()
                                # cannot solve frequency send in a short time due to the lib implementation
                                msg_content = await sendGIF(cur, sticker_path)
                            elif(msg_instance.media.document.mime_type == "audio/ogg"):
                                tag = "audio"
                                audio_path = await client.download_media(msg_instance)
                                with open(audio_path, 'rb') as file:
                                    oga_data = file.read()
                                    msg_content = base64.b64encode(
                                        oga_data).decode()
                                os.remove(audio_path)
                            elif(msg_instance.media.document.mime_type == 'application/pdf'):
                                tag = "pdf"
                                print(
                                    f"message URL : https://t.me/c/{channel_id}/{msg_instance.id}")
                        else:
                            msg_content = msg_instance.message
                            tag = "message"
                            # to address the quote in msg
                            msg_content.replace("\"", "\\\"")
                    except Exception as e:
                        print(e)
                        print(msg_instance)
                        print(msg_content)

                    # get the time when the message has been sent
                    msg_time: Timestamp = msg_instance.date

                    obj = {
                        "tag": tag,
                        "channel": channel_id,
                        "from": sender,
                        "data": msg_content,
                        "message_id": msg_instance.id,  # save the message id for advanced functions
                        "timestamp": str(msg_time)
                    }
                    context.append(obj)

                message = {
                    "code": 200,
                    "context": context
                }
            except Exception as e:
                print(e)
                message = {"code": 500, "error": e}
                print("channel_not_found")
        else:
            message = {"code": 400, "error": "System : You are not connected"}
    return message


@app.websocket('/conn')
async def conn():
    while True:
        phone = await websocket.receive()
        client = TelegramClient(phone, api_id, api_hash)
        await client.connect()
        # login part
        if not await client.is_user_authorized():
            try:
                await client.send_code_request(phone)
                sys = {
                    'tag': 'system',
                    'context': 'please enter code received in your telegram app'
                }
                sys = str(sys).replace('\'', '\"')
                await websocket.send(sys)
                # Code = await websocket.receive()
                Code = input(f"Code for {phone} : ")
                await client.sign_in(phone, Code)
            except:
                sys = {
                    'tag': 'system',
                    'context': 'Invalid phone number'
                }
                sys = str(sys).replace('\'', '\"')
                await websocket.send(sys)
                sys = {
                    'tag': 'system',
                    'context': 'login aborted'
                }
                sys = str(sys).replace('\'', '\"')
                await websocket.send(sys)
                return

        me = await client.get_me()

        sys = {
            "tag": "system",
            "context": f"Login as {me.id}"
        }

        sys = str(sys).replace('\'', '\"')

        await websocket.send(str(sys))

        # searching PoS
        async for message in client.iter_messages('testing', search='vava'):
            continue
            # print(message.id,message)

        # search by id
        async for message in client.iter_messages('Telegram', ids=7):
            continue
            # print(message.id, message)

        # get the unread counts while user is offline
        dialogs: list[telethon.Dialog] = await client.get_dialogs()
        x = []
        for d in dialogs:
            if(type(d.message.peer_id) == telethon.tl.types.PeerChannel):
                x.append([d.unread_count, d.message.peer_id.channel_id])
            elif(type(d.message.peer_id) == telethon.tl.types.PeerChat):
                x.append([d.unread_count, d.message.peer_id.chat_id])
            else:
                x.append([d.unread_count, d.message.peer_id.user_id])

        for e in x:
            unread = {
                "tag": "initial",
                "channel": e[1],
                "count": e[0]
            }
            unread = str(unread).replace("\'", "\"")
            await websocket.send(unread)

        # insert current user into user list
        print(type(me.id))
        global client_list
        client_list[me.id] = client

        # initial database
        if(not get_dialog.check_user_existence(me.id)):
            await get_dialog.get(client_list[me.id])
            await get_dialog.initial_info(me.id)

        # get client info
        font_size, language = await get_dialog.retrieve_info(me.id)
        info = {
            'tag': 'system',
            'font_size': font_size,
            'language': language,
            'context': f'font_size = {font_size}, language = {language}'
        }
        info = str(info).replace('\'', '\"')
        await websocket.send((info))

        # send images
        channels: list[int] = await get_dialog.retrive_all(me.id)
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

        # hook on the incoming messages
        @client_list[me.id].on(events.NewMessage())
        async def handler(event):
            print(event.message)

            channel: telethon.Channel = await event.get_chat()

            channel_id: int = channel.id
            try:
                sender_instance: telethon.Peer = await event.get_sender()
                if sender_instance.username != None:
                    sender = sender_instance.username
                elif sender_instance.first_name != None:
                    lname = sender_instance.last_name if sender_instance.last_name != None else ""
                    sender = sender_instance.first_name + lname
                else:
                    sender = sender_instance.title
            except:  # for those channels containing anonymous users
                sender = channel.title

            time_stamp = event.message.date
            if type(event.message.media) == telethon.tl.types.MessageMediaPhoto:
                tag = "image"
                # download the photo enclosed with the message
                image_path = await client.download_media(event.message)
                # convert the photo archieve to base64
                with open(image_path, 'rb') as file:
                    image_data = file.read()
                    data = base64.b64encode(image_data).decode()
                os.remove(image_path)
            # tgs ** to be solved ** , mp4 file **solved**
            elif type(event.message.media) == telethon.tl.types.MessageMediaDocument:
                # the rcv data is a mp4 (gif on the telegram perspective)
                if(event.message.media.document.mime_type == "video/mp4"):
                    tag = "mp4"
                    sticker_path = await client.download_media(event.message)
                    with open(sticker_path, 'rb') as file:
                        mp4_data = file.read()
                        # convert mp4 into b64
                        data = base64.b64encode(mp4_data).decode()
                    os.remove(sticker_path)
                # its a telegram sticker (.tgs file)
                elif(event.message.media.document.mime_type == "application/x-tgsticker"):
                    tag = "gif"
                    # use the library to convert .tgs to .gif; The frontend will need to specific the gif extension in tag
                    sticker_path = await client.download_media(event.message)
                    # convert .tgs to .gif
                    cur = time.time_ns()

                    # cannot solve frequency send in a short time due to the lib implementation
                    data = await sendGIF(cur, sticker_path)
                elif(event.message.media.document.mime_type == "audio/ogg"):
                    tag = "audio"
                    audio_path = await client.download_media(event.message)
                    with open(audio_path, 'rb') as file:
                        oga_data = file.read()
                        data = base64.b64encode(oga_data).decode()
                        print(data)
                    os.remove(audio_path)
                elif(event.message.media.document.mime_type == 'application/pdf'):
                    tag = "pdf"
                    print(
                        f"message URL : https://t.me/c/{channel_id}/{event.message.id}")  # the URL only work for public channel

            else:
                tag = "message"
                data = event.message.message
                data = data.replace("\\", "\\\\")
                data = data.replace("\"", "\\\"")

            # print(data,end="\n\n\n")
            obj = {
                "tag": tag,
                "channel": channel_id,
                "from": sender,
                "data": data,
                "time_stamp": str(time_stamp)
            }
            obj = str(obj)
            obj = obj.replace("\\\'", "\'")
            obj = obj.replace(", '", ', "').replace("',", '",')
            obj = obj.replace(": '", ': "').replace("':", '":')
            obj = obj.replace("{'", '{"').replace("'}", '"}')
            obj = obj.replace("\\\\", "\\")
            # print(obj,end="\n\n")
            await websocket.send(obj)
            # PoS : Read message
            '''try:
                await client.send_read_acknowledge(channel_id.id,event.message)
            except:
                await client.send_read_acknowledge(channel_id.title,event.message)'''

        await client_list[me.id].run_until_disconnected()


@app.websocket('/pri')
async def pri():
    while True:
        data = await websocket.receive()
        pri = json.loads(data)
        user = int(pri["user_id"])
        global client_list
        key = utils.find_client(user, client_list)
        if key != -1:
            client = client_list[key]
            if client.is_connected():
                priority_pair: tuple[int, int] = json.loads(data)
                print(priority_pair["channel"], priority_pair["pri"])
                await get_dialog.set_pri(priority_pair["channel"], priority_pair["pri"])
                await websocket.send(f'System : set priority of {priority_pair["channel"]} to {priority_pair["pri"]}')
        else:
            await websocket.send("System : You are not Connected!")


@app.websocket('/ws')
async def ws():
    while True:
        data = await websocket.receive()
        pair = json.loads(data)
        user = int(pair["user_id"])
        global client_list
        key = utils.find_client(user, client_list)
        if key != -1:
            client = client_list[key]
            if client.is_connected():
                try:
                    id = pair["channel"]
                    name = await client.get_entity(int(id))
                    print(name)
                    await client.send_message(entity=name, message=pair["message"])
                    await websocket.send(f'{pair["channel"]} : {pair["message"]}')
                    print("message sent")
                except:
                    await websocket.send(f'you can\'t write in this channel ({pair["channel"]})')
            else:
                await websocket.send("System : You are not Connected!")


@app.websocket('/disconnect')
async def disconnect():
    while True:
        data = await websocket.receive()
        dis = json.loads(data)
        user = int(dis["user_id"])
        global client_list
        key = utils.find_client(user, client_list)
        if key != -1:
            client = client_list[key]

            print("disconnect!")

            await client.disconnect()
            await websocket.send("System : Disconnected")
        else:
            await websocket.send("System : Client not exists")


async def test():
    await pyrlottie.convSingleLottie(lottieFile=pyrlottie.LottieFile("AnimatedSticker.tgs"), destFiles=[f'a.gif'])


if __name__ == "__main__":
    asyncio.run(app.run_task())
    # asyncio.run(test())
