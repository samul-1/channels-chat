from django import forms
from chat.models import Colorset, Profile, Attachment
from django.forms import ModelForm
from django.utils.safestring import mark_safe

class MessageForm(forms.Form):
	msg_text = forms.CharField(label="Your message", widget=forms.TextInput(attrs={'size': '100', 'style': 'margin-left: 5px', 'id': 'message-input'}))

class ColorsetForm(forms.Form):
	selection = forms.ModelChoiceField(label="Select theme:", widget=forms.Select(attrs={'style': 'margin-left: 5px', 'onchange': 'this.form.submit()'}), queryset=Colorset.objects.all(), empty_label=None)

class AttachmentForm(ModelForm):
	class Meta:
		model = Attachment
		fields = ['file']
		labels = {
			'file': mark_safe('<i style="font-size: 200%" class="fas fa-paperclip"></i>')
		}