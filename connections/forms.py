from django import forms
from .models import DirectMessage


class DirectMessageForm(forms.ModelForm):
    """Form for sending direct messages between connected users"""
    
    class Meta:
        model = DirectMessage
        fields = ['content', 'attachment']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Type your message here...',
                'required': True
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif'
            })
        }
        labels = {
            'content': 'Message',
            'attachment': 'Attachment (optional)'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = True
        self.fields['attachment'].required = False
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if content:
            content = content.strip()
            if len(content) < 1:
                raise forms.ValidationError("Message cannot be empty.")
            if len(content) > 1000:
                raise forms.ValidationError("Message is too long. Maximum 1000 characters allowed.")
        return content
    
    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            # Check file size (max 5MB)
            if attachment.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size cannot exceed 5MB.")
            
            # Check file extension
            allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif']
            file_extension = attachment.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError("File type not allowed. Allowed types: PDF, DOC, DOCX, JPG, JPEG, PNG, GIF.")
        
        return attachment