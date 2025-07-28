from django import forms
from .messaging_models import Message

class MessageForm(forms.ModelForm):
    """
    Form for sending messages in conversations
    """
    class Meta:
        model = Message
        fields = ['content', 'attachment']
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Type your message...',
                'autocomplete': 'off'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = True
        self.fields['attachment'].required = False