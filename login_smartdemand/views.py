from django.shortcuts import render


# Create your views here.


def login_view(request):
    return render(request, 'users/login_page.html')

def register_view(request):
    return render(request, 'users/register_page.html')
