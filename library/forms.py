from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class StyledUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        placeholders = {
            "username": "Username",
            "first_name": "First name",
            "last_name": "Last name",
            "email": "Email address",
            "password1": "Password",
            "password2": "Confirm password",
        }

        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "class": "form-control form-control-lg",
                    "placeholder": placeholders.get(name, ""),
                }
            )