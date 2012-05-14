from django import forms


class CreateGroupForm(forms.Form):
    group = forms.CharField()
    code = forms.CharField()
