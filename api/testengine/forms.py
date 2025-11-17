# evaluation/forms.py

from django import forms
from .models import Question


class EvaluationForm(forms.Form):
    """
    Dinamikusan generált űrlap egy adott kérdőív-típushoz (pl. diák → tanár).
    """

    def __init__(self, *args, questionnaire_type: str = None, **kwargs):
        super().__init__(*args, **kwargs)

        if questionnaire_type is None:
            raise ValueError("questionnaire_type megadása kötelező az EvaluationForm-hoz.")

        # Aktív kérdések lekérdezése a megfelelő irányhoz
        questions = Question.objects.filter(
            questionnaire_type=questionnaire_type,
            is_active=True,
        ).order_by("order", "id")

        self.questions = questions           # a view-nek mentjük
        self.question_fields = []            # a template-nek: (field_name, question) párok

        for question in questions:
            field_name = f"q_{question.id}"

            if question.question_type == "scale":
                choices = [(i, str(i)) for i in range(question.scale_min, question.scale_max + 1)]
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
