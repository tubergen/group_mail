from django import forms


class CreateGroupForm(forms.Form):
    email = forms.EmailField(required=False)
    code = forms.CharField()
