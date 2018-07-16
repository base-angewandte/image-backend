from django.urls import path
from artworkusers.views import *

urlpatterns = [
    path('<int:id>.html', details, name='user_details'),
]
