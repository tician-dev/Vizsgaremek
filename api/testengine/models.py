# evaluation/models.py

from django.conf import settings
from django.db import models


# ---------- Choice-ok ----------

ROLE_CHOICES = (
    ("teacher", "Tanár"),
    ("student", "Diák"),
)

QUESTIONNAIRE_TYPE_CHOICES = (
    ("student_to_teacher", "Diák → Tanár"),
    ("teacher_to_student", "Tanár → Diák"),
)

QUESTION_TYPE_CHOICES = (
    ("scale", "Likert skála (1–5)"),
    ("text", "Szöveges válasz"),
)


# ---------- Dimenziók (pl. Kommunikáció, Fegyelmezettség) ----------

class Dimension(models.Model):
    """Értékelési dimenzió: pl. Kommunikáció, Felkészültség, Igazságosság."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    # Opcionális: melyik szerepre vonatkozik elsősorban (tanár/diák)
    target_role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        blank=True,
        null=True,
        help_text="Ha csak tanárra vagy csak diákra értelmes ez a dimenzió, itt megadhatod.",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


# ---------- Kérdések ----------

class Question(models.Model):
    """
    Egy értékelő kérdés / állítás.
    Lehet skálás (1-5) vagy szöveges.
    """

    text = models.TextField()
    dimension = models.ForeignKey(
        Dimension,
        on_delete=models.CASCADE,
        related_name="questions",
        null=True,
        blank=True,
        help_text="Szöveges kérdésnél opcionális.",
    )
    questionnaire_type = models.CharField(
        max_length=30,
        choices=QUESTIONNAIRE_TYPE_CHOICES,
        help_text="Milyen irányú értékelő ívben jelenik meg (diák→tanár / tanár→diák)?",
    )
    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPE_CHOICES,
        default="scale",
    )
    # Skála paraméterek (Likert)
    scale_min = models.PositiveSmallIntegerField(default=1)
    scale_max = models.PositiveSmallIntegerField(default=5)

    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["questionnaire_type", "order", "id"]

    def __str__(self):
        return f"[{self.get_questionnaire_type_display()}] {self.text[:60]}"


# ---------- Egy kitöltés (ki, kit értékelt, mikor, milyen kontextusban?) ----------

class Evaluation(models.Model):
    """
    Egy konkrétan kitöltött kérdőív:
    - KI (rater) KIT (evaluated) értékelt
    - milyen irányban (diák→tanár / tanár→diák)
    - milyen kontextusban (pl. Tantárgy, félév, osztály)
    """

    questionnaire_type = models.CharField(
        max_length=30,
        choices=QUESTIONNAIRE_TYPE_CHOICES,
    )

    # KI töltötte ki (értékelő személy)
    rater = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="given_evaluations",
    )

    # KIT értékeltek (tanár vagy diák)
    evaluated = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_evaluations",
    )

    # Értékelt személy szerepe (tanár/diák)
    evaluated_role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
    )

    # Konkrét kontextus (egyszerűen, szöveggel)
    context = models.CharField(
        max_length=255,
        blank=True,
        help_text="Pl. 2024/25 1. félév, Matematika, 10.A",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # Opcionális: anonim-e a kitöltés (pl. diák→tanár)
    is_anonymous = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_questionnaire_type_display()} - {self.evaluated} ({self.created_at.date()})"


# ---------- Válaszok egy-egy kérdésre ----------

class Answer(models.Model):
    """
    Egy konkrét válasz egy kérdésre egy Evaluation-ön belül.
    Skálás kérdésnél value_int, szövegesnél value_text van kitöltve.
    """

    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
    )

    # Skálás válasz (pl. 1–5)
    value_int = models.IntegerField(null=True, blank=True)

    # Szöveges válasz
    value_text = models.TextField(blank=True)

    class Meta:
        unique_together = ("evaluation", "question")

    def __str__(self):
        return f"Válasz #{self.pk} (Eval {self.evaluation_id}, Q {self.question_id})"
