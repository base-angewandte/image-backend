from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    tos_accepted = models.BooleanField(default=False)

    class Meta:
        db_table = 'auth_user'
