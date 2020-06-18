import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.utils import timezone, dateformat
from datetime import timedelta
from .models import Message, Profile
import time

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']
        self.room_group_name = 'chat'

        # set user as online
        this_user = Profile.objects.get(of_user=self.scope["user"].pk)
        this_user.is_online = True
        this_user.save()

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        # only show the entrance message if the user wasn't online already
        if(this_user.just_left == False):
            msg = Message()
            msg.msg_text = " joined the chatroom"
            msg.sent_by = self.scope["user"]
            msg.is_system_message = True
            msg.save()

            # Send user entered message
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'user_entered',
                    'username': self.scope["user"].username,
                }
            )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

        # set user as not online in db
        this_user = Profile.objects.get(of_user=self.scope["user"].pk)
        this_user.is_online = False
        this_user.just_left = True
        this_user.save()

        time.sleep(5)
        this_user = Profile.objects.get(of_user=self.scope["user"].pk)

        # Send user left message only if the user hasn't come back
        if(this_user.is_online == False):
            msg = Message()
            msg.msg_text = " left the chatroom"
            msg.sent_by = self.scope["user"]
            msg.is_system_message = True
            msg.save()

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'username': self.scope["user"].username,
                }
            )
        # user has now left the room completely
        this_user.just_left = False
        this_user.save()

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        msg_type = text_data_json['type']

        this_user = Profile.objects.get(of_user=self.scope["user"].pk)
        
        # check if user is still connected
        if(this_user.is_online == True):
        # Send message to room group
            if(msg_type == 'user'):
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sent_by': self.scope["user"].username,
                        'timestamp': dateformat.format(timezone.now() + timedelta(hours=2), 'H:i')
                    }
                )
                # save message to db
                msg = Message()
                msg.msg_text = message
                msg.sent_by = self.scope["user"]
                msg.save()

    # message type handlers:

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']
        sent_by = event['sent_by']
        timestamp = event['timestamp']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message_type': 'chat_message',
            'message': message,
            'sent_by': sent_by,
            'timestamp': timestamp
        }))

    def user_entered(self, event):
        username = event['username']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message_type': 'user_joined',
            'username': username,
            'timestamp': dateformat.format(timezone.now() + timedelta(hours=2), 'H:i')
        }))
    
    def user_left(self, event):
        username = event['username']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message_type': 'user_left',
            'username': username,
            'timestamp': dateformat.format(timezone.now() + timedelta(hours=2), 'H:i')
        }))