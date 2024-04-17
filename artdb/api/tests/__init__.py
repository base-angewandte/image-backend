from rest_framework.test import APITestCase as RestFrameworkAPITestCase

from django.contrib.auth import get_user_model


class APITestCase(RestFrameworkAPITestCase):
    def setUp(self):
        # create and log in user
        User = get_user_model()
        self.user = User.objects.create_user('temporary', 'temporary@uni-ak.ac.at')
        self.client.force_login(self.user)
