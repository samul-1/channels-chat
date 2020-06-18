from django import forms
from chat.models import Colorset, Profile

class MessageForm(forms.Form):
	msg_text = forms.CharField(label="Your message", widget=forms.TextInput(attrs={'size': '100', 'style': 'margin-left: 5px', 'id': 'message-input'}))

class ColorsetForm(forms.Form):
	selection = forms.ModelChoiceField(label="Select theme", widget=forms.Select(attrs={'style': 'margin-left: 5px', 'onchange': 'this.form.submit()'}), queryset=Colorset.objects.all(), empty_label=None)