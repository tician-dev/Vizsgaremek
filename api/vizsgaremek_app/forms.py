from django import forms
from .models import Question
from django.contrib.auth.forms import UserCreationForm   # 🔹 EZ KELL
from django.contrib.auth import get_user_model 

User = get_user_model()


class EvaluationForm(forms.Form):
    """
    Dinamikusan generált űrlap egy adott kérdőív-típushoz (pl. diák → tanár),
    opcionálisan kérdéstípus (scale / text) szerinti szűréssel.
    """

    def __init__(
        self,
        *args,
        questionnaire_type: str = None,
        question_type_filter: str | None = None,  # <-- ÚJ
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if questionnaire_type is None:
            raise ValueError("questionnaire_type megadása kötelező az EvaluationForm-hoz.")

        qs = Question.objects.filter(
            questionnaire_type=questionnaire_type,
            is_active=True,
        )

        if question_type_filter is not None:
            qs = qs.filter(question_type=question_type_filter)

        questions = qs.order_by("order", "id")

        self.questions = questions
        self.question_fields = []

        for question in questions:
            field_name = f"q_{question.id}"

            if question.question_type == "scale":
                choices = [
                    (i, str(i))
                    for i in range(question.scale_min, question.scale_max + 1)
                ]
                field = forms.ChoiceField(
                    label=question.text,
                    choices=choices,
                    widget=forms.RadioSelect,
                    required=True,
                )
            else:  # "text"
                field = forms.CharField(
                    label=question.text,
                    widget=forms.Textarea(attrs={"rows": 3}),
                    required=False,
                )

            self.fields[field_name] = field
            self.question_fields.append((field_name, question))


class RegisterForm(UserCreationForm):
    ROLE_CHOICES = (
        ("student", "Diák"),
        ("teacher", "Tanár"),
    )

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label="Szerep",
        widget=forms.RadioSelect,
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "role")