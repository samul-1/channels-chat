from django.shortcuts import render, redirect
from .forms import MessageForm, ColorsetForm, AttachmentForm
from .models import Message, Colorset, Profile, Room, Attachment
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
import datetime
from django.contrib.auth import logout, authenticate, login
from django.utils import timezone, dateformat
from django.db.models import Q
import logging

# Create your views here.

from django.http import HttpResponse, HttpRequest, HttpResponseRedirect

def index(request):
    return HttpResponse("Hello, world. You're at the chat index. <a href='chat'>Click here</a>.")
  
def upload(request):
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            # file is saved
            form.save()
            logging.warning(request.FILES)
            return HttpResponseRedirect('/chat/welcome')
    else:
        form = AttachmentForm()
    return render(request, 'chat/upload.html', {'form': form})

@login_required
def chatroom(request, invisible=False):
  
  today = timezone.now().date()
  # gets colorset preference for this user
  try:
    colorset = Profile.objects.get(of_user = request.user.pk).selected_colorset
  except Profile.DoesNotExist:
    # if user doesn't have a preference set, choose the default colorset and add a db preference for this user
    # THIS SHOULD NEVER HAPPEN BECAUSE PREFERENCES GET CREATED AT SIGN UP TIME
    colorset = Colorset.objects.get(pk=1)
    profile = Profile()
    profile.of_user = request.user
    # profile.selected_colorset = Colorset.objects.get(pk=1)
    profile.save()

  # form to upload attachments
  if request.method == 'POST':
    attachment_form = AttachmentForm(request.POST, request.FILES)
    if attachment_form.is_valid():
      # file is saved
      attachment = attachment_form.save()
      attachment.uploaded_by = request.user
      attachment.save()
      #return HttpResponseRedirect('/chat/welcome')
  else:
    logging.warning("NO")
    attachment_form = AttachmentForm()
  
  if Profile.objects.get(of_user=request.user.pk).is_banned:
    return render(request, "chat/banned.html")

  if invisible and not request.user.groups.filter(name = "Operator").exists():
    invisible = False

  # instantiate colorset selection form
  colorset_selection = ColorsetForm(initial={'selection': colorset.pk})

  # get all the conversations where user is a participant
  rooms = Room.objects.filter(Q(user_1=request.user) | Q(user_2=request.user))
  
  # only send the username of the other user in private conversation to webpage for rendering
  rooms_with_adjusted_title = list(rooms)

  for room in rooms_with_adjusted_title:
    if room.user_1 == request.user:
      room.title = room.user_2.username
    else:
      room.title = room.user_1.username
  
  if request.user.groups.filter(name = "Operator").exists():
    # get all messages
    messages = Message.objects.filter(Q(in_room=1) | Q(in_room__in=rooms)) #.order_by('timestamp')[:10]
  else:
    messages = {}
  
  # set user as online
  this_user = Profile.objects.get(of_user=request.user)
  this_user.is_online = True
  this_user.save()

  # get online users list
  online_users = Profile.objects.filter(Q(is_online=True) & Q(is_visible=True))

  return render(request, "chat/chatroom.html", {'messages': messages, 'colorform': colorset_selection, 'today': today, 'colorset': colorset.filename, 'online_users': online_users, 'rooms': rooms_with_adjusted_title, 'invisible': invisible, 'attachment_form': attachment_form})

# @login_required
# def invisible(request):
#   if request.user.groups.filter(name = "Operator").exists():
#     return HttpResponseRedirect(chatroom, invisible=True)
#   return redirect(chatroom)

@login_required
def welcome(request):
  # if Profile.objects.get(of_user=request.user.pk).is_banned:
  #   return render(request, "chat/banned.html")
  online_user_count = Profile.objects.filter(Q(is_online=True) & Q(is_visible=True)).count()

  return render(request, "chat/welcome.html", {'user_count': online_user_count})

def features(request):
  return render(request, "chat/features.html")

# create an account
def register(request):
  if request.method == "POST":
    # process form data
    form = UserCreationForm(request.POST)
    if form.is_valid():
      user = form.save()
      login(request, user)
      defaultColorSetId = 1
      profile = Profile()
      profile.of_user = request.user
      # set default colorset preference
      profile.selected_colorset = Colorset.objects.get(pk=defaultColorSetId)
      profile.save()
      return redirect("/chat/")
    else:
      for msg in form.error_messages:
        print(form.error_messages[msg])

      return render(request, "registration/register.html", {"form":form})

  form = UserCreationForm
  return render(request, "registration/register.html", {"form":form})

def user_logout(request):
  user_profile = Profile.objects.get(of_user=request.user)
  user_profile.is_online = False
  user_profile.save()
  return HttpResponseRedirect('/accounts/logout')

def set_theme(request):
  if request.method == 'POST':
    form = ColorsetForm(data=request.POST)
    if form.is_valid():
      profile = Profile.objects.get(of_user=request.user)
      # update user preference
      profile.selected_colorset = form.cleaned_data['selection']
      profile.save()
  return HttpResponseRedirect('/chat/')

# import time
# from django.http import StreamingHttpResponse
# from datetime import timedelta

# def stream(request):
#     def event_stream():
#         while True:
#             time.sleep(1)
#             right_now = timezone.now()
#             queryset = Message.objects.filter(timestamp__gt=right_now - timedelta(seconds=1))
#             for message in queryset:
#               ts = dateformat.format(right_now + timedelta(hours=2),  'H:i')
#               yield 'data: <span class="msg others_msg">%s: %s <i class="timestamp">%s</i></span>\n\n' % (message.sent_by, message.msg_text, ts)
#     return StreamingHttpResponse(event_stream(), content_type='text/event-stream')