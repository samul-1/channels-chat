from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.

from django.contrib.auth.models import User

class Room(models.Model):
    """
    A room for people to chat in.
    """

    # Room title
    title = models.CharField(max_length=255)

    # only "staff" users are allowed? (is_staff on django's User)
    staff_only = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False) # if False, this is a private conversation between user_1 and user_2
    user_1 = models.ForeignKey(User, on_delete=models.CASCADE, null=True, default=None, related_name="user_1")
    user_2 = models.ForeignKey(User, on_delete=models.CASCADE, null=True, default=None, related_name="user_2")

    def __str__(self):
        return self.title

    @property
    def group_name(self):
        """
        Returns the Channels Group name that sockets should subscribe to to get sent
        messages as they are generated.
        """
        return "room-%s" % self.id


class Message(models.Model):
	sent_by = models.ForeignKey(User, on_delete=models.CASCADE)
	msg_text = models.TextField()
	timestamp = models.DateTimeField(default=timezone.now) #auto_now_add=True
	is_system_message = models.BooleanField(default=False)
	is_server_message = models.BooleanField(default=False)
	in_room = models.ForeignKey(Room, on_delete=models.CASCADE, default=1)
	def __str__(self):
		return self.msg_text

class Colorset(models.Model):
	name = models.CharField(max_length=100)
	filename = models.CharField(max_length=20)
	def __str__(self):
		return self.name

class Language(models.Model):
    name = models.CharField(max_length=30)
    code = models.CharField(max_length=2)
    def __str__(self):
        return self.name

class Profile(models.Model):
    of_user = models.ForeignKey(User, on_delete=models.CASCADE)
    selected_colorset = models.ForeignKey(Colorset, on_delete=models.SET_DEFAULT, default=1)
    selected_language = models.ForeignKey(Language, on_delete=models.SET_DEFAULT, default=1)
    is_online = models.BooleanField(default=False)
    just_left = models.BooleanField(default=False)
    was_kicked = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    is_muted = models.BooleanField(default=False)
    sound_notification_enabled = models.BooleanField(default=True)
    def __str__(self):
        return self.of_user.username

class Attachment(models.Model):
    file = models.FileField(upload_to='')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, default=None, related_name="uploaded_by")
    timestamp = models.DateTimeField(default=timezone.now)
    dispatched = models.BooleanField(default=False) # has the attachment already been sent to the chat (True) or has it just been uploaded and waiting for the server to receive the message (False)?