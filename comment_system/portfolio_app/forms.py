from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    content = forms.CharField(label= "", widget=forms.Textarea(
        attrs={
            'placeholder': 'Add a comment...',
            'class': 'form-control',
            'rows': 3,
            'style': 'resize: none;'
        }
    ))
    class Meta:
        model = Comment
        fields = ['content']