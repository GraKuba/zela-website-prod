from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    return render(request, 'website/home.html', {
        'title': 'Zela - Home',
    })