from django.shortcuts import render 

def home(request):
    return render(request, 'home.html')

def login(request):
    return render(request, 'registration/login.html')

def logout(request):
    return render(request, 'registration/logged_out.html')

def register(request):
    return render(request, 'registration/register.html')

def profile(request):
    return render(request, 'profile.html')