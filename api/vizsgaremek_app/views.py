from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from testengine.engine import ( EvaluationEngine,EvaluationInput,RatingSummary,TextFeedback,ObjectiveData, )


# Other views
def home(request):
    return render(request, 'home.html')

# Authentication views
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sikeres regisztráció! Most be tudsz jelentkezni.')
            return redirect('login')
        else:
            # Hibák megjelenítése és lefordítása magyarúra
            for field, errors in form.errors.items():
                for error in errors:
                    error_msg = str(error)
                    
                    # Fordítások
                    if "already exists" in error_msg or "exists" in error_msg:
                        messages.error(request, 'Felhasználónév már foglalt!')
                    elif "password" in error_msg.lower() and "common" in error_msg.lower():
                        messages.error(request, 'A jelszó túl általános. Válassz erősebb jelszót!')
                    elif "password" in error_msg.lower() and "similar" in error_msg.lower():
                        messages.error(request, 'A jelszó túl hasonló a felhasználónévhez!')
                    elif "password" in error_msg.lower() and "numeric" in error_msg.lower():
                        messages.error(request, 'A jelszó nem lehet csak számokból álló!')
                    elif "password" in error_msg.lower() and "short" in error_msg.lower():
                        messages.error(request, 'A jelszó legalább 8 karakter hosszú kell legyen!')
                    else:
                        messages.error(request, f'{error_msg}')
            return render(request, 'registration/register.html', {'form': form})
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Hibás felhasználónév vagy jelszó!')
        else:
            messages.error(request, 'Hibás felhasználónév vagy jelszó!')
        return render(request, 'registration/login.html', {'form': form})
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def profile(request):
    """Bejelentkezett felhasználó profilja"""
    return render(request, 'registration/profile.html')

def logout(request):
    auth_logout(request)
    return redirect('home')


# Debug view - ellenőrizze a bejelentkezés állapotát
def debug(request):
    """Debug view - user információ kijelzése"""
    context = {
        'is_authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else 'Anonymous',
        'user_id': request.user.id if request.user.is_authenticated else None,
        'session_key': request.session.session_key,
    }
    return JsonResponse(context)

def evaluation(request):
    
    # Itt a DB-ből összegyűjtöd az adott személy értékeléseit,
    # majd feltöltöd vele az EvaluationInput-ot.

    #data = EvaluationInput(
    #    evaluated_id=1,
    #    evaluated_name="Kiss Péter",
    #    evaluated_role="teacher",  # vagy "student"
    #    context="2024/25 1. félév, Matematika",
    #    ratings=[
    #        RatingSummary(dimension="Kommunikáció", self_score=4.2, others_score=3.8),
    #        RatingSummary(dimension="Felkészültség", self_score=4.5, others_score=4.3),
    #    ],
    #    texts=[
    #        TextFeedback(
    #            source_type="student",
    #            question_label="Mi az, amit különösen értékelsz a tanár óráin?",
    #            content="Nagyon érthetően magyaráz, sok példával."
    #        ),
    #        TextFeedback(
    #            source_type="student",
    #            question_label="Min lenne érdemes javítani?",
    #            content="Néha túl gyorsan megy végig az anyagon."
    #        ),
    #    ],
    #    objective_data=[
    #        ObjectiveData(label="Átlagos óralátogatás", value="95%"),
    #    ],
    #)
#
    #engine = EvaluationEngine(model="gpt-4o", reasoning_effort="medium")
    #feedback_text = engine.generate_feedback(data)
    return render(request, 'evaluation.html')








