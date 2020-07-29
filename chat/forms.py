from django import forms
from chat.models import Colorset, Profile, Attachment, Language
from django.forms import ModelForm, FileInput
from django.utils.safestring import mark_safe

class MessageForm(forms.Form):
	msg_text = forms.CharField(label="Your message", widget=forms.TextInput(attrs={'size': '100', 'style': 'margin-left: 5px', 'id': 'message-input'}))

class ColorsetForm(forms.Form):
	selection = forms.ModelChoiceField(label="", widget=forms.Select(attrs={'style': 'margin-left: 5px', 'onchange': 'this.form.submit()'}), queryset=Colorset.objects.all(), empty_label=None)

class LanguageForm(forms.Form):
	selection = forms.ModelChoiceField(label="", widget=forms.Select(attrs={'id': '', 'style': 'margin-left: 5px', 'onchange': 'this.form.submit()'}), queryset=Language.objects.all(), empty_label=None)

class AttachmentForm(ModelForm):
	class Meta:
		model = Attachment
		fields = ['file']
		widgets = {
			'file': FileInput(attrs={'onchange': 'validateSize(file)'})
		}
		labels = {
			'file': mark_safe('')
		}