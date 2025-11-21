from django.shortcuts import render, redirect, get_object_or_404 , render
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .forms import EvaluationForm, RegisterForm
from .models import Evaluation, Answer
from django.contrib.auth import get_user_model
from .engine import EvaluationEngine
from django.contrib.auth.models import Group


# Other views
def home(request):
    return render(request, 'home.html')

# Authentication views
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            role = form.cleaned_data["role"]  # "student" vagy "teacher"

            # Csoport hozzárendelés
            try:
                group_name = "teacher" if role == "teacher" else "student"
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
            except Group.DoesNotExist:
                # Ha nincs ilyen group, akkor egyszerűen nem csinálunk semmit
                pass
            messages.success(request, "Sikeres regisztráció! Most már bejelentkezhetsz.")
            return redirect("login")
            
    else:
        form = RegisterForm()

    return render(request, "registration/register.html", {"form": form})

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


@login_required
def evaluate_teacher(request, teacher_id):
    questionnaire_type = "student_to_teacher"
    teacher = get_object_or_404(User, pk=teacher_id)
    evaluator = request.user

    # --- Szerveroldali védelem ---
    same_user = (evaluator == teacher)
    same_group = teacher.groups.filter(
        id__in=evaluator.groups.values_list("id", flat=True)
    ).exists()

    if same_user or same_group:
        messages.error(
            request,
            "Nem értékelheted önmagad vagy a saját csoportodba tartozó felhasználókat."
        )
        return redirect("teacher_list")  # vagy 'home'

    if request.method == "POST":
        form = EvaluationForm(
            request.POST,
            questionnaire_type=questionnaire_type,
            evaluator=evaluator,
            evaluated_user=teacher,
        )
        if form.is_valid():
            evaluation = Evaluation.objects.create(
                questionnaire_type=questionnaire_type,
                rater=evaluator,
                evaluated=teacher,
                evaluated_role="teacher",
                context="2024/25 1. félév, általános értékelés",
                is_anonymous=True,
            )

            for question in form.questions:
                field_name = f"q_{question.id}"
                raw_value = form.cleaned_data.get(field_name)

                if question.question_type == "scale":
                    Answer.objects.create(
                        evaluation=evaluation,
                        question=question,
                        value_int=int(raw_value) if raw_value is not None else None,
                    )
                else:
                    Answer.objects.create(
                        evaluation=evaluation,
                        question=question,
                        value_text=raw_value or "",
                    )

            return redirect("evaluation_thanks")
    else:
        form = EvaluationForm(
            questionnaire_type=questionnaire_type,
            evaluator=evaluator,
            evaluated_user=teacher,
        )

    return render(
        request,
        "evaluation/evaluate_teacher.html",
        {"form": form, "teacher": teacher},
    )


User = get_user_model()


@login_required
def evaluation(request, teacher_id=None):
    """
    1. lépés: strukturált pontozás (Likert).
    Csak a question_type='scale' kérdéseket jeleníti meg.
    """

    questionnaire_type = "student_to_teacher"

    if teacher_id is None:
        messages.error(request, "Először válaszd ki, melyik tanárt szeretnéd értékelni.")
        return redirect("teacher_list")

    teacher = get_object_or_404(User, pk=teacher_id)
    evaluator = request.user

    # --- tiltás: önmaga / saját csoport ---
    same_user = (evaluator == teacher)
    same_group = teacher.groups.filter(
        id__in=evaluator.groups.values_list("id", flat=True)
    ).exists()

    if same_user or same_group:
        messages.error(
            request,
            "Nem értékelheted önmagad vagy a saját csoportodba tartozó felhasználókat."
        )
        return redirect("teacher_list")

    if request.method == "POST":
        form = EvaluationForm(
            request.POST,
            questionnaire_type=questionnaire_type,
            question_type_filter="scale",
            evaluator=evaluator,
            evaluated_user=teacher,
        )
        if form.is_valid():
            evaluation = Evaluation.objects.create(
                questionnaire_type=questionnaire_type,
                rater=evaluator,
                evaluated=teacher,
                evaluated_role="teacher",
                context="2024/25 1. félév, általános értékelés",
                is_anonymous=True,
            )

            for question in form.questions:
                field_name = f"q_{question.id}"
                raw_value = form.cleaned_data.get(field_name)

                Answer.objects.create(
                    evaluation=evaluation,
                    question=question,
                    value_int=int(raw_value) if raw_value is not None else None,
                )

            return redirect("evaluation_open", evaluation_id=evaluation.id)
    else:
        form = EvaluationForm(
            questionnaire_type=questionnaire_type,
            question_type_filter="scale",
            evaluator=evaluator,
            evaluated_user=teacher,
        )

    question_fields = [
        (form[field_name], question)
        for field_name, question in form.question_fields
    ]

    return render(
        request,
        "evaluation/evaluate_teacher.html",
        {
            "form": form,
            "teacher": teacher,
            "question_fields": question_fields,
        },
    )
    
@login_required
def evaluation_open(request, evaluation_id):
    """
    2. lépés: nyitott, szöveges visszajelzések.
    Ugyanahhoz az Evaluation-höz menti a text típusú válaszokat.
    """

    evaluation = get_object_or_404(Evaluation, pk=evaluation_id, rater=request.user)
    questionnaire_type = evaluation.questionnaire_type
    teacher = evaluation.evaluated
    evaluator = request.user

    if request.method == "POST":
        form = EvaluationForm(
            request.POST,
            questionnaire_type=questionnaire_type,
            question_type_filter="text",
            evaluator=evaluator,
            evaluated_user=teacher,
        )
        if form.is_valid():
            for question in form.questions:
                field_name = f"q_{question.id}"
                raw_value = form.cleaned_data.get(field_name)

                Answer.objects.create(
                    evaluation=evaluation,
                    question=question,
                    value_text=raw_value or "",
                )

            return redirect("evaluation_thanks")
    else:
        form = EvaluationForm(
            questionnaire_type=questionnaire_type,
            question_type_filter="text",
            evaluator=evaluator,
            evaluated_user=teacher,
        )

    question_fields = [
        (form[field_name], question)
        for field_name, question in form.question_fields
    ]

    return render(
        request,
        "evaluation/evaluate_teacher_open.html",
        {
            "form": form,
            "teacher": teacher,
            "evaluation": evaluation,
            "question_fields": question_fields,
        },
    )
    
    
def evaluation_thanks(request):
    return render(request, "evaluation/thanks.html")

@login_required
def teacher_report(request, teacher_id):
    """
    Tanár összesített szöveges értékelése (GPT által generált).
    - teacher_id: az értékelt tanár User.id-je
    """
    User = get_user_model()
    teacher = get_object_or_404(User, pk=teacher_id)

    # Ha szeretnél konkrét kontextusra szűrni (pl. félév + tantárgy), itt add meg:
    # context_str = "2024/25 1. félév, Matematika"
    context_str = None  # Most: minden elérhető értékelés összevonva

    engine = EvaluationEngine(model="gpt-5.1")  
    feedback_text = engine.generate_feedback_for_teacher(
        teacher=teacher,
        context=context_str,
    )

    return render(
        request,
        "evaluation/teacher_report.html",
        {
            "teacher": teacher,
            "context_str": context_str,
            "feedback_text": feedback_text,
        },
    )




@login_required
def teacher_list(request):
    """
    Tanárok listája – innen lehet kiválasztani, kit szeretne a diák értékelni.
    Feltételezzük, hogy a tanárok a 'teacher' csoportban vannak.
    """
    try:
        teacher_group = Group.objects.get(name="teacher")
        teachers = (
            User.objects
            .filter(groups=teacher_group)
            .exclude(id=request.user.id)                      # önmagát ne lássa
            .exclude(groups__in=request.user.groups.all())   # saját csoportját ne lássa
            .distinct()
        )
    except Group.DoesNotExist:
        teachers = User.objects.none()

    return render(
        request,
        "evaluation/teacher_list.html",
        {"teachers": teachers},
    )