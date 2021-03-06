from django.contrib import admin
from .models import Message, Profile, Colorset, Room, Attachment, Language

# Register your models here.

class MessageAdmin(admin.ModelAdmin):
	list_display = ('msg_text', 'sent_by', 'timestamp', 'in_room')

class ProfileAdmin(admin.ModelAdmin):
	list_display = ('of_user', 'selected_colorset', 'selected_language')

class ColorsetAdmin(admin.ModelAdmin):
	list_display = ('name', 'filename')

class RoomAdmin(admin.ModelAdmin):
	list_display = ('title', 'pk')

class AttachmentAdmin(admin.ModelAdmin):
	list_display = ('file', 'uploaded_by', 'dispatched', 'timestamp')

class LanguageAdmin(admin.ModelAdmin):
	list_display = ('name', 'code')

admin.site.register(Message, MessageAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Colorset, ColorsetAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(Language, LanguageAdmin)