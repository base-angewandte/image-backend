from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from artworks.models import *


# TODO: currently not used. delete?
def details(request, id=None):
    context = {}
    context['title'] = 'User Details'
    context['user'] = get_object_or_404(User, id=id)
    return render(request, 'artworkusers/details.html', context)