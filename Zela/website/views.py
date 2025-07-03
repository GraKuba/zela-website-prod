from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    return render(request, 'website/home.html', {
        'title': 'Zela - Home',
    })

def about(request):
    return render(request, 'website/components/page-about/about.html', {
        'title': 'About Zela - Attention and care for your home',
    })

def blog(request):
    return render(request, 'website/components/page-blog/blog.html', {
        'title': 'Zela Blog - Tips, news and household inspiration',
    })

def contact(request):
    return render(request, 'website/components/page-contact/contact.html', {
        'title': 'Contact Zela - Get in Touch',
    })