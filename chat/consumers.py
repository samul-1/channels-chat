# import json
# from asgiref.sync import async_to_sync
# from channels.generic.websocket import WebsocketConsumer
from django.utils import timezone, dateformat
from datetime import timedelta
from .models import Message, Profile, Room, Attachment
import time
from django.contrib.auth.models import User, Group
from asgiref.sync import sync_to_async
import logging
from django.conf import settings

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .exceptions import ClientError
from .utils import get_room_or_error

from channels.db import database_sync_to_async
import asyncio

from django.db.models import Q

class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    This chat consumer handles websocket connections for chat clients.

    It uses AsyncJsonWebsocketConsumer, which means all the handling functions
    must be async functions, and any sync work (like ORM access) has to be
    behind database_sync_to_async or sync_to_async. For more, read
    http://channels.readthedocs.io/en/latest/topics/consumers.html
    """

    ##### WebSocket event handlers

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        await asyncio.sleep(0.5) # REMOVE THIS IN PRODUCTION
        # Are they logged in?
        if self.scope["user"].is_anonymous:
            # Reject the connection
            await self.close()
        else:
            # Accept the connection
            await self.accept()

        # Store which rooms the user has joined on this connection
        self.rooms = set()

        # join all the rooms user is a participant of
        for room in await sync_to_async(list)(Room.objects.filter(Q(user_1=self.scope["user"]) | Q(user_2=self.scope["user"]))):
            try:
                await self.join_room(str(room.pk))
            except ClientError:
                pass
        await self.set_as_online(self.scope["user"])

    async def receive_json(self, content):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # Messages will have a "command" key we can switch on
        command = content.get("command", None)

        if not await self.is_online(self.scope["user"]): # if for some reason an offline user sends a message, kill that connection
            await self.close()
            return

        try:
            if command == "join":
                # Make them join the room
                await self.join_room(content["room"], content["invisible"])
            elif command == "leave":
                # Leave the room
                await self.leave_room(content["room"])
            elif command == "send":
                await self.send_room(content["room"], content["message"])
            elif command == "attachment":
                await self.send_attachment(content["room"])
            elif command == "kick":
                await self.kick_user(content["room"], content["who_kicked"], content["kicked_user"], content["ban"])
            elif command == "new_private_msg":
                await self.create_private_conversation(content["message"], content["recipient"])
            elif command == "toggle_mute":
                await self.toggle_mute(content["target"], content["room"])
            elif command == "toggle_sound_notification":
                await self.toggle_sound_notification()
        except ClientError as e:
            # Catch any errors and send it back
            await self.send_json({"error": e.code})

    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """

        # set user as not online in db
        await self.set_just_left(self.scope["user"])
        
        # wait 3 seconds and check if user has come back
        await asyncio.sleep(3)

        # Send user left message only if the user hasn't come back
        # Leave all the rooms we are still in
        for room_id in list(self.rooms):
            try:
                await self.leave_room(room_id)
            except ClientError:
                pass
        
        # user is not in "just left" status anymore
        await self.clear_user_status(self.scope["user"])

    ##### Command helper methods called by receive_json

    async def join_room(self, room_id, invisible='0'):
        """
        Called by receive_json when someone sent a join command.
        """
        # if the user is just coming back after having left a few seconds ago, do nothing        
        room = await get_room_or_error(room_id, self.scope["user"])
        logging.warning(invisible)
        if(not await self.had_left(self.scope["user"]) and room_id == '1'):
            # Send a join message if it's turned on -- if entering in invisible mode, don't sent "user joined" message
            if settings.NOTIFY_USERS_ON_ENTER_OR_LEAVE_ROOMS and (not invisible == '1' or not await self.is_operator(self.scope["user"])):
                await self.channel_layer.group_send(
                    room.group_name,
                    {
                        "type": "chat.join",
                        "room_id": room_id,
                        "username": self.scope["user"].username,
                        "timestamp": dateformat.format(timezone.now() + timedelta(hours=2), "H:i")
                    }
                )
                await self.save_message(" joined the chatroom", self.scope["user"], True)
        # Store that we're in the room
        self.rooms.add(room_id)
        # Add them to the group so they get room messages
        await self.channel_layer.group_add(
            room.group_name,
            self.channel_name,
        )
        # Instruct their client to finish opening the room
        await self.send_json({
            "operation": "join",
            "join": str(room.id),
            "title": room.title,
        })

        # Make us invisible to other users if using invisible mode (only for operators)
        if invisible == '1' and await self.is_operator(self.scope["user"]):
            await self.set_invisible(self.scope["user"])
        if invisible == '-1':
            await self.set_visible(self.scope["user"])
    
    async def create_private_conversation(self, message, recipient):
        recipient_user = await self.get_user_by_username(recipient)
        
        # if a private conversation between the two users doesn't exist, create such a room
        room = await self.get_private_room_or_none(self.scope["user"], recipient_user)
        if(room == None):
            room = await self.new_private_room(self.scope["user"], recipient_user)
            main_room = await get_room_or_error('1', self.scope["user"])
            await self.channel_layer.group_send(
                    main_room.group_name,
                    {
                        "type": "chat.newconv",
                        "room_id": room.pk,
                        "username": self.scope["user"].username,
                        "recipient": recipient
                    }
            )
        logging.warning(self.rooms)
        # add sender to private room channel
        if str(room.pk) not in self.rooms:
            await self.join_room(str(room.pk))
        await self.send_room(str(room.pk), message)

    async def leave_room(self, room_id):
        """
        Called by receive_json when someone sent a leave command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware
        room = await get_room_or_error(room_id, self.scope["user"])
        # Send a leave message if it's turned on
        if(not await self.has_come_back(self.scope["user"]) and not await self.was_kicked(self.scope["user"])):
            if settings.NOTIFY_USERS_ON_ENTER_OR_LEAVE_ROOMS:
                await self.channel_layer.group_send(
                    room.group_name,
                    {
                        "type": "chat.leave",
                        "room_id": room_id,
                        "username": self.scope["user"].username,
                        "timestamp": dateformat.format(timezone.now() + timedelta(hours=2), "H:i")
                    }
                )
            if room_id == '1' and await self.is_visible(self.scope["user"]):
                await self.save_message(" left the chatroom", self.scope["user"], True)
            if room_id != '1':
                await self.delete_room(room_id)

        # Remove that we're in the room
        self.rooms.discard(room_id)
        # Remove them from the group so they no longer get room messages
        await self.channel_layer.group_discard(
            room.group_name,
            self.channel_name,
        )
        # Instruct their client to finish closing the room
        await self.send_json({
            "operation": "leave",
            "leave": str(room.id),
        })

    async def send_room(self, room_id, message):
        """
        Called by receive_json when someone sends a message to a room.
        """

        logging.warning(room_id)
        logging.warning(self.rooms)
        # Check they are in this room
        if room_id not in self.rooms:
            raise ClientError("ROOM_ACCESS_DENIED")
        # Check if they are muted
        if room_id == '1' and await self.is_muted(self.scope["user"]):
            return
        # Get the room and send to the group about it
        room = await get_room_or_error(room_id, self.scope["user"])
        await self.save_message(message, self.scope["user"], False, room_id)
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.message",
                "room_id": room_id,
                "username": self.scope["user"].username,
                "message": message,
                "timestamp": dateformat.format(timezone.now() + timedelta(hours=2), "H:i")
            }
        )
    
    async def send_attachment(self, room_id):
        """
        Called by receive_json when someone uploads an attachment.
        """

        # logging.warning(room_id)
        # logging.warning(self.rooms)
        # Check they are in this room
        if room_id not in self.rooms:
            raise ClientError("ROOM_ACCESS_DENIED")
        # Get the room and send to the group about it
        room = await get_room_or_error(room_id, self.scope["user"])
        await asyncio.sleep(1)
        attachment = await self.get_attachment_or_none(self.scope["user"])
        logging.warning(attachment)
        if attachment == None:
            raise ClientError("FILE_DOES_NOT_EXIST")
        # await self.save_message(message, self.scope["user"], False, room_id)
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.attachment",
                "room_id": room_id,
                "username": self.scope["user"].username,
                "url": attachment.file.url,
                "size": attachment.file.size,
                "timestamp": dateformat.format(timezone.now() + timedelta(hours=2), "H:i")
            }
        )
        await self.set_attachment_dispatched(attachment)
    
    async def kick_user(self, room_id, who_kicked, kicked_user, ban):
        """
        Called by receive_json when an operator kicks a user
        """
         # Check they are in this room and if they are an operator
        if room_id not in self.rooms or not await self.is_operator(self.scope["user"]):
            raise ClientError("ROOM_ACCESS_DENIED")
        # Get the room and send to the group about it
        room = await get_room_or_error(room_id, self.scope["user"])
        if(await self.is_operator(self.scope["user"])):
            await self.channel_layer.group_send(
                room.group_name,
                {
                    "type": "chat.kick",
                    "room_id": room_id,
                    "kicked_user": kicked_user,
                    "who_kicked": who_kicked,
                    "timestamp": dateformat.format(timezone.now() + timedelta(hours=2), "H:i")
                }
            )
        if ban == '1':
            await self.set_ban(await self.get_user_by_username(kicked_user))

    async def toggle_mute(self, target, room_id):
        """
        Called by receive_json when an operator wants to mute/unmute a user
        """
        
        # Check they are in this room and if they are an operator
        if room_id not in self.rooms or not await self.is_operator(self.scope["user"]):
            raise ClientError("ROOM_ACCESS_DENIED")

        room = await get_room_or_error(room_id, self.scope["user"])

        new_status = await self.db_toggle_muted(await self.get_user_by_username(target))
        
        if(await self.is_operator(self.scope["user"])):
            await self.channel_layer.group_send(
                room.group_name,
                {
                    "type": "chat.mute",
                    "target": target,
                    "new_status": new_status,
                    "timestamp": dateformat.format(timezone.now() + timedelta(hours=2), "H:i")
                }
            )


    ##### Handlers for messages sent over the channel layer

    # These helper methods are named by the types we send - so chat.join becomes chat_join
    async def chat_join(self, event):
        """
        Called when someone has joined our chat.
        """
        if not await self.is_online(self.scope["user"]): # if for some reason an offline user is supposed to receive a message, kill that connection
            await self.close()
            return
        # Send a message down to the client
        await self.send_json(
            {
                "msg_type": 4, #settings.MSG_TYPE_ENTER,
                "room": event["room_id"],
                "username": event["username"],
                "timestamp": event["timestamp"],
            },
        )

    async def chat_leave(self, event):
        """
        Called when someone has left our chat.
        """
        if not await self.is_online(self.scope["user"]): # if for some reason an offline user is supposed to receive a message, kill that connection
            await self.close()
            return
        # Send a message down to the client
        await self.send_json(
            {
                "msg_type": 5, #settings.MSG_TYPE_LEAVE,
                "room": event["room_id"],
                "username": event["username"],
                "timestamp": event["timestamp"],
            },
        )

    async def chat_message(self, event):
        """
        Called when someone has messaged our chat.
        """
        if not await self.is_online(self.scope["user"]): # if for some reason an offline user is supposed to receive a message, kill that connection
            await self.close()
            return
        # Send a message down to the client
        await self.send_json(
            {
                "msg_type": 0, #settings.MSG_TYPE_MESSAGE,
                "room": event["room_id"],
                "username": event["username"],
                "message": event["message"],
                "timestamp": event["timestamp"],
            },
        )

    async def chat_attachment(self, event):
        """
        Called when someone has messaged our chat.
        """
        if not await self.is_online(self.scope["user"]): # if for some reason an offline user is supposed to receive a message, kill that connection
            await self.close()
            return
        # Send a message down to the client
        await self.send_json(
            {
                "msg_type": 6,
                "room": event["room_id"],
                "username": event["username"],
                "url": event["url"],
                "size": event["size"],
                "timestamp": event["timestamp"],
            },
        )

    async def chat_kick(self, event):
        """
        Called when someone has kicked a user
        """
        if not await self.is_online(self.scope["user"]): # if for some reason an offline user is supposed to receive a message, kill that connection
            await self.close()
            return
        # Send a message down to the client
        await self.send_json(
            {
                "msg_type": 2, #settings.MSG_TYPE_ALERT,
                "kicked_user": event["kicked_user"],
                "who_kicked": event["who_kicked"],
                "timestamp": event["timestamp"],
            },
        )
        if(self.scope["user"].username == event['kicked_user']):
            await self.set_kicked(self.scope["user"])
            await self.close()

    async def chat_mute(self, event):
        """
        Called when someone has muted/unmuted a user
        """
        if not await self.is_online(self.scope["user"]): # if for some reason an offline user is supposed to receive a message, kill that connection
            await self.close()
            return
        # Send a message down to the client
        await self.send_json(
            {
                "msg_type": 7,
                "target": event["target"],
                "new_status": event["new_status"],
                "timestamp": event["timestamp"],
            },
        )
    
    async def chat_newconv(self, event):
        """
        Called when someone initiates a new private conversation with another user
        """
        if not await self.is_online(self.scope["user"]): # if for some reason an offline user is supposed to receive a message, kill that connection
            await self.close()
            return
        # add recipient to private conversation channel
        if(self.scope["user"].username == event["recipient"] or self.scope["user"].username == event["username"]):
            await self.join_room(str(event["room_id"]))
            # Send a message down to the client
            await self.send_json(
                {
                    "msg_type": 3, #settings.MSG_TYPE_MUTED,
                    "room": event["room_id"],
                    "username": event["username"],
                    "recipient": event["recipient"]
                },
            )

    @database_sync_to_async
    def save_message(self, message, username, is_system=False, in_room=None):
        msg = Message()
        msg.msg_text = message
        msg.sent_by = username
        msg.is_system_message = is_system
        if(in_room != None):
            msg.in_room = Room.objects.get(pk=in_room)
        msg.save()
    
    @database_sync_to_async
    def set_just_left(self, user):
        this_user = Profile.objects.get(of_user=user.pk)
        this_user.is_online = False
        this_user.just_left = True
        this_user.save()

    @database_sync_to_async
    def has_come_back(self, user):
        this_user = Profile.objects.get(of_user=user.pk)
        return this_user.is_online
    
    @database_sync_to_async
    def had_left(self, user):
        this_user = Profile.objects.get(of_user=user.pk)
        return this_user.just_left
    
    @database_sync_to_async
    def set_kicked(self, user):
        this_user = Profile.objects.get(of_user=user.pk)
        this_user.was_kicked = True
        this_user.save()
    
    @database_sync_to_async
    def was_kicked(self, user):
        this_user = Profile.objects.get(of_user=user.pk)
        return this_user.was_kicked
    
    @database_sync_to_async
    def clear_user_status(self, user):
        this_user = Profile.objects.get(of_user=user.pk)
        this_user.just_left = False
        this_user.was_kicked = False
        this_user.is_visible = True
        if not this_user.is_online:
            this_user.is_muted = False
        this_user.save()
    
    @database_sync_to_async
    def is_online(self, user):
        logging.warning(Profile.objects.get(of_user=user).is_online)
        return Profile.objects.get(of_user=user).is_online

    @database_sync_to_async
    def set_as_online(self, user):
        this_user = Profile.objects.get(of_user=user.pk)
        this_user.is_online = True
        this_user.save()

    @database_sync_to_async
    def is_operator(self, user):
        this_user = User.objects.get(pk=user.pk)
        return this_user.groups.filter(name='Operator').exists()

    @database_sync_to_async
    def new_private_room(self, user1, user2):
        room = Room()
        room.title = user1.username + "-" + user2.username
        room.user_1 = user1
        room.user_2 = user2
        room.save()
        return room
    
    @database_sync_to_async
    def get_user_by_username(self, name):
        return User.objects.get(username=name)

    @database_sync_to_async
    def get_private_room_or_none(self, user1, user2):
        try:
            room = Room.objects.get(Q(user_1=user1) & Q(user_2=user2) | Q(user_1=user2) & Q(user_2=user1))
        except Room.DoesNotExist:
            return None

        return room

    @database_sync_to_async
    def is_visible(self, user):
        this_user = Profile.objects.get(of_user=user.pk)
        return this_user.is_visible
    
    @database_sync_to_async
    def set_invisible(self, user):
        this_user = Profile.objects.get(of_user=user.pk)
        this_user.is_visible = False
        this_user.save()

    @database_sync_to_async
    def set_visible(self, user):
        this_user = Profile.objects.get(of_user=user.pk)
        this_user.is_visible = True
        this_user.save()
    
    @database_sync_to_async
    def set_ban(self, to_ban):
        user = Profile.objects.get(of_user=to_ban.pk)
        user.is_banned = True
        user.save()

    @database_sync_to_async
    def get_attachment_or_none(self, user):
        try:
            file = Attachment.objects.get(Q(uploaded_by=user) & Q(dispatched=False))
        except Attachment.DoesNotExist:
            return None
        return file

    @database_sync_to_async
    def set_attachment_dispatched(self, attachment):
        file = Attachment.objects.get(pk=attachment.pk)
        file.dispatched = True
        file.save()
    
    @database_sync_to_async
    def delete_room(self, room_id):
        room = Room.objects.get(pk=room_id).delete()

    @database_sync_to_async
    def is_muted(self, user):
        this_user = Profile.objects.get(of_user=user.pk)
        return this_user.is_muted
    
    @database_sync_to_async
    def db_toggle_muted(self, user):
        this_user = Profile.objects.get(of_user=user.pk)
        this_user.is_muted = not this_user.is_muted
        this_user.save()
        return this_user.is_muted
    
    @database_sync_to_async
    def toggle_sound_notification(self):
        this_user = Profile.objects.get(of_user=self.scope["user"])
        this_user.sound_notification_enabled = not this_user.sound_notification_enabled
        this_user.save()