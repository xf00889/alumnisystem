from django import forms
from .models import DirectMessage, DirectConversation


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


class GroupPhotoUploadForm(forms.ModelForm):
    """Form for uploading group photos for group conversations"""

    class Meta:
        model = DirectConversation
        fields = ['group_photo']
        widgets = {
            'group_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'groupPhotoInput'
            })
        }
        labels = {
            'group_photo': 'Group Photo'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group_photo'].required = True
        self.fields['group_photo'].help_text = "Upload a group photo (JPG, PNG, GIF). Max size: 5MB"

    def clean_group_photo(self):
        group_photo = self.cleaned_data.get('group_photo')
        if group_photo:
            # Check file size (max 5MB)
            if group_photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File size cannot exceed 5MB.")

            # Check if it's an image
            if not group_photo.content_type.startswith('image/'):
                raise forms.ValidationError("File must be an image (JPG, PNG, GIF).")

            # Check file extension
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            file_extension = group_photo.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError("File type not allowed. Allowed types: JPG, JPEG, PNG, GIF.")

        return group_photo