# evaluation/admin.py

from django.contrib import admin
from .models import Dimension, Question, Evaluation, Answer , School

class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ("text", "questionnaire_type", "question_type", "dimension", "order", "is_active")
    show_change_link = True


@admin.register(Dimension)
class DimensionAdmin(admin.ModelAdmin):
    list_display = ("name", "target_role", "order")
    list_filter = ("target_role",)
    ordering = ("order", "name")
    search_fields = ("name",)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("short_text", "questionnaire_type", "question_type", "dimension", "order", "is_active")
    list_filter = ("questionnaire_type", "question_type", "dimension", "is_active")
    ordering = ("questionnaire_type", "order", "id")
    search_fields = ("text",)

    def short_text(self, obj):
        return (obj.text[:60] + "...") if len(obj.text) > 60 else obj.text
    short_text.short_description = "Kérdés"


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ("question", "value_int", "value_text")


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("id", "questionnaire_type", "rater", "evaluated", "evaluated_role", "context", "created_at", "is_anonymous")
    list_filter = ("questionnaire_type", "evaluated_role", "is_anonymous", "created_at")
    search_fields = (
        "context",
        "rater__username",
        "rater__first_name",
        "rater__last_name",
        "evaluated__username",
        "evaluated__first_name",
        "evaluated__last_name",
    )
    ordering = ("-created_at",)
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "evaluation", "question", "value_int", "short_text")
    list_filter = ("question__questionnaire_type", "question__question_type")
    search_fields = ("value_text", "question__text")

    def short_text(self, obj):
        if not obj.value_text:
            return ""
        return (obj.value_text[:40] + "...") if len(obj.value_text) > 40 else obj.value_text
    short_text.short_description = "Szöveges válasz"
