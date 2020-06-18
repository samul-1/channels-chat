from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.

from django.contrib.auth.models import User

class Message(models.Model):
	sent_by = models.ForeignKey(User, on_delete=models.CASCADE)
	msg_text = models.TextField()
	timestamp = models.DateTimeField(default=timezone.now) #auto_now_add=True
	is_system_message = models.BooleanField(default=False)
	is_server_message = models.BooleanField(default=False)
	def __str__(self):
		return self.msg_text

class Colorset(models.Model):
	name = models.CharField(max_length=100)
	filename = models.CharField(max_length=20)
	def __str__(self):
		return self.name

class Profile(models.Model):
	of_user = models.ForeignKey(User, on_delete=models.CASCADE)
	selected_colorset = models.ForeignKey(Colorset, on_delete=models.CASCADE, default=1)
	is_online = models.BooleanField(default=False)
	just_left = models.BooleanField(default=False)
	def __str__(self):
		return self.of_user.username