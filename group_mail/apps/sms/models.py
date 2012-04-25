from django.db import models
from django.contrib.auth.models import User, UserManager


class CustomUser(User):
    phone_number = models.CharField(max_length=20)

    objects = UserManager()
