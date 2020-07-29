from django.shortcuts import render, redirect
from .forms import MessageForm, ColorsetForm, AttachmentForm, LanguageForm
from .models import Message, Colorset, Profile, Room, Attachment
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
import datetime
from django.contrib.auth import logout, authenticate, login
from django.utils import timezone, dateformat
from django.db.models import Q
import logging
import json
from django.utils.safestring import SafeString
import os.path
import requests
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect

def index(request):
    return HttpResponse("Hello, world. You're at the chat index. <a href='chat'>Click here</a>.")
  
# def upload(request):
#     if request.method == 'POST':
#         form = AttachmentForm(request.POST, request.FILES)
#         if form.is_valid():
#             # file is saved
#             form.save()
#             logging.warning(request.FILES)
#             return HttpResponseRedirect('/chat/welcome')
#     else:
#         form = AttachmentForm()
#     return render(request, 'chat/upload.html', {'form': form})

@login_required
def chatroom(request, invisible=False):
  today = timezone.now().date()
  # gets colorset preference for this user
  try:
    colorset = Profile.objects.get(of_user = request.user.pk).selected_colorset
    curr_language = Profile.objects.get(of_user = request.user.pk).selected_language
  except Profile.DoesNotExist:
    # if user doesn't have a preference set, choose the default colorset and add a db preference for this user
    # THIS SHOULD NEVER HAPPEN BECAUSE PREFERENCES GET CREATED AT SIGN UP TIME--IT'S JUST FOR DEBUGGING FOR MANUALLY CREATED USERS
    colorset = Colorset.objects.get(pk=1)
    profile = Profile()
    profile.of_user = request.user
    # profile.selected_colorset = Colorset.objects.get(pk=1)
    profile.save()

  # check if user is banned
  if Profile.objects.get(of_user=request.user.pk).is_banned:
    return render(request, "chat/banned.html")

  invisible = request.POST.get("invisible", False)
  # check if user is trying to use invisible mode but is not an operator
  if invisible and not request.user.groups.filter(name = "Operator").exists():
    invisible = False


  # form to upload attachments
  if request.method == 'POST': # attachment was uploaded
    attachment_form = AttachmentForm(request.POST, request.FILES)
    # checks for size limit and only saves file if user is online (otherwise the attachment couldn't be dispatched because user cannot send attachment message to websocket)
    if attachment_form.is_valid() and request.FILES["file"].size <= 5000000 and Profile.objects.get(of_user=request.user).is_online: 
      # file is saved
      attachment = attachment_form.save()
      attachment.uploaded_by = request.user
      attachment.save()
  else:
    attachment_form = AttachmentForm()

  # instantiate colorset selection form
  colorset_selection = ColorsetForm(initial={'selection': colorset.pk})

  # instantiate language selection form
  language_selection = LanguageForm(initial={'selection': curr_language.pk})

  # import language file
  json_lang = requests.get('http://127.0.0.1:8000/static/chat/lang.json').json()

  # get all the conversations that user is a participant of
  rooms = Room.objects.filter(Q(user_1=request.user) | Q(user_2=request.user))
  
  # only send the username of the other user in private conversation to webpage for rendering
  rooms_with_adjusted_title = list(rooms)

  for room in rooms_with_adjusted_title:
    if room.user_1 == request.user:
      room.title = room.user_2.username
    else:
      room.title = room.user_1.username
  
  # if request.user.groups.filter(name = "Operator").exists():
  #   # get all messages
  #   messages = Message.objects.filter(Q(in_room=1) | Q(in_room__in=rooms)) #.order_by('timestamp')[:10]
  # else:
  messages = {} # don't retrieve old messages (can easily be changed for message persistence)
  
  # set user as online
  this_user = Profile.objects.get(of_user=request.user)
  this_user.is_online = True
  this_user.save()

  # get online users list
  online_users = Profile.objects.filter(Q(is_online=True) & Q(is_visible=True))

  # get my profile
  my_profile = Profile.objects.get(of_user=request.user)

  return render(request, "chat/chatroom.html", {
    'messages': messages,
    'my_profile': my_profile,
    'colorform': colorset_selection,
    'languageform': language_selection, 
    'today': today, 
    'colorset': colorset.filename, 
    'jsonLang': json_lang[curr_language.code], 
    'currLang': curr_language.code, 
    'online_users': online_users, 
    'rooms': rooms_with_adjusted_title, 
    'invisible': invisible, 
    'attachment_form': attachment_form
  })

# @login_required
# def invisible(request):
#   if request.user.groups.filter(name = "Operator").exists():
#     return HttpResponseRedirect(chatroom, invisible=True)
#   return redirect(chatroom)

@login_required
def welcome(request):
  # if Profile.objects.get(of_user=request.user.pk).is_banned:
  #   return render(request, "chat/banned.html")
  this_user = Profile.objects.get(of_user=request.user)
  online_user_count = Profile.objects.filter(Q(is_online=True) & Q(is_visible=True)).count()
  colorset = Profile.objects.get(of_user = request.user.pk).selected_colorset

  return render(request, "chat/welcome.html", {
    'user_count': online_user_count,
    'this_user': this_user,
    'colorset': colorset.filename
  })

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

def set_language(request):
  if request.method == 'POST':
    form = LanguageForm(data=request.POST)
    if form.is_valid():
      profile = Profile.objects.get(of_user=request.user)
      # update user preference
      profile.selected_language = form.cleaned_data['selection']
      profile.save()
  return HttpResponseRedirect('/chat/')

def online_users_count(request):
  online_user_count = Profile.objects.filter(Q(is_online=True) & Q(is_visible=True)).count()
  return HttpResponse(online_user_count)

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