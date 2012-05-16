from django.db import models
from django.contrib.auth.models import User, UserManager


class CustomUser(User):
    phone_number = models.CharField(max_length=20)

    objects = UserManager()


class Group(models.Model):
    MAX_LEN = 20
    name = models.CharField(max_length=MAX_LEN, unique=True)
    code = models.CharField(max_length=MAX_LEN)
    members = models.ManyToManyField(CustomUser, related_name='memberships')
    admins = models.ManyToManyField(CustomUser)

    def __unicode__(self):
        return self.name
