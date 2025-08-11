from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    # La note sera alimentée par les étoiles cliquables côté UI
    rating = forms.IntegerField(min_value=1, max_value=5, widget=forms.HiddenInput())

    class Meta:
        model = Review
        fields = ["rating", "title", "comment"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "w-full border rounded px-3 py-2",
                    "placeholder": "Titre de votre avis",
                    "required": True,
                }
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "w-full border rounded px-3 py-2",
                    "rows": 4,
                    "placeholder": "Partagez votre expérience...",
                    "required": True,
                }
            ),
        }


