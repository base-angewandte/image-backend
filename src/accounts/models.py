from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    tos_accepted = models.BooleanField(default=False)

    class Meta:
        db_table = 'auth_user'

    def __str__(self):
        return self.get_full_name() or self.username
