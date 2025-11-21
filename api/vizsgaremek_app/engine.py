from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Literal, Optional, List
import os
from django.contrib.auth import get_user_model
from django.db.models import Avg
from openai import OpenAI
import openai  # az exception típusok miatt
from .models import Dimension, Question, Evaluation, Answer, ObjectiveMetric


@dataclass
class RatingSummary:
    """
    Egy dimenzió (pl. Kommunikáció) numerikus összefoglalása.
    self_score: tanár önértékelése (ha lesz ilyen később)
    others_score: diákok / mások átlagos pontszáma
    """

    dimension: str
    self_score: Optional[float]
    others_score: Optional[float]
    scale_min: int = 1
    scale_max: int = 5


@dataclass
class TextFeedback:
    """
    Szöveges visszajelzés (pl. diák nyitott kérdésre adott válasza).
    """
    
    source_type: Literal["student", "teacher", "other"]
    text: str


@dataclass
class ObjectiveData:
    """
    Objektív mutatók (pl. jegyátlag, bukási arány).
    """

    label: str
    value: Any


@dataclass
class EvaluationInput:
    """
    A nyelvi modell felé küldött teljes input struktúra.
    """

    evaluated_id: int
    evaluated_name: str
    evaluated_role: Literal["teacher", "student"]
    context: str

    ratings: List[RatingSummary]
    texts: List[TextFeedback]
    objective_data: List[ObjectiveData]


# ---------- Az engine osztály ----------


class EvaluationEngine:
    """
    Tanár/diák értékelések kiértékeléséért felelős "engine".

    Fő használat:
        engine = EvaluationEngine()
        summary_text = engine.generate_feedback_for_teacher(user_obj, context="2024/25 1. félév")
    """

    def __init__(self,model: str = "gpt-5.1",) -> None:
        """
        model: API modellnév. Ha nincs GPT-5.1 hozzáférésed,
               átírhatod pl. "gpt-4o"-ra.
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),)
        self.model = model

    # ---------- Publikus: tanárra aggregált feedback ----------

    def generate_feedback_for_teacher(self,teacher,context: Optional[str] = None,) -> str:
        """
        Teljes folyamat:
        - ORM-ből összegyűjti az adott tanárra vonatkozó értékeléseket
        - EvaluationInput objektummá alakítja
        - Meghívja a GPT modellt, és visszaad egy szöveges értékelést

        Ha nincs adat, egy rövid tájékoztató szöveget ad vissza.
        """
        data = self.build_input_for_teacher(teacher, context=context)

        if data is None:
            return (
                "Ehhez a tanárhoz még nem érkezett értékelés ebben a kontextusban, "
                "ezért nem tudok érdemi visszajelzést adni."
            )

        return self.generate_feedback(data)

    # ---------- ORM → EvaluationInput ----------

    def build_input_for_teacher(self,teacher,context: Optional[str] = None,questionnaire_type: str = "student_to_teacher",) -> Optional[EvaluationInput]:
        """
        Django ORM-ből összegyűjti az adott tanárra vonatkozó adatokat,
        és visszaad egy EvaluationInput objektumot.

        questionnaire_type: pl. "student_to_teacher" vagy később más.
        """

        User = get_user_model()

        if not isinstance(teacher, User):
            raise TypeError("teacher paraméternek Django User példánynak kell lennie.")

        # 1) Összes értékelés, ami erre a tanárra vonatkozik
        eval_qs = Evaluation.objects.filter(
            evaluated=teacher,
            evaluated_role="teacher",
            questionnaire_type=questionnaire_type,
        )
        if context:
            eval_qs = eval_qs.filter(context=context)

        eval_qs = eval_qs.order_by("-created_at")

        if not eval_qs.exists():
            return None

        # 2) Numerikus értékelések dimenziónként (Likert-skála)
        ratings = self._build_ratings(eval_qs, questionnaire_type)

        # 3) Nyitott szöveges visszajelzések
        texts = self._build_text_feedbacks(eval_qs)

        # 4) Objektív mutatók
        objective_data = self._build_objective_data(eval_qs)

        # 5) Kontextus szöveg
        if context:
            ctx_str = context
        else:
            ctx_str = "Összes elérhető értékelés (minden kontextus összevonva)."

        evaluated_name = (
            teacher.get_full_name()
            if hasattr(teacher, "get_full_name") and teacher.get_full_name()
            else str(teacher)
        )

        return EvaluationInput(
            evaluated_id=teacher.id,
            evaluated_name=evaluated_name,
            evaluated_role="teacher",
            context=ctx_str,
            ratings=ratings,
            texts=texts,
            objective_data=objective_data,
        )

    def _build_ratings(self, eval_qs, questionnaire_type: str) -> List[RatingSummary]:
        """
        Dimenziónként átlagos pontszámok (diákok értékelése).
        Jelenleg self_score = None (nincs önértékelés).
        """

        # Minden skálás kérdés, amely
        # - ehhez a kérdőív-típushoz tartozik
        # - van rá válasz az adott Evaluation-ök között
        scale_questions = (
            Question.objects.filter(
                questionnaire_type=questionnaire_type,
                question_type="scale",
                answers__evaluation__in=eval_qs,
            )
            .exclude(dimension__isnull=True)
            .distinct()
        )

        if not scale_questions.exists():
            return []

        ratings: List[RatingSummary] = []

        # Milyen dimenziók jelennek meg a skálás kérdések között?
        dim_ids = scale_questions.values_list("dimension_id", flat=True).distinct()
        dimensions = Dimension.objects.filter(id__in=dim_ids)

        for dim in dimensions:
            dim_q_ids = scale_questions.filter(dimension=dim).values_list(
                "id", flat=True
            )

            agg = (
                Answer.objects.filter(
                    evaluation__in=eval_qs,
                    question_id__in=dim_q_ids,
                )
                .exclude(value_int__isnull=True)
                .aggregate(avg=Avg("value_int"))
            )

            avg_score = agg["avg"]

            if avg_score is None:
                continue

            # Feltételezzük, hogy 1–5-ös skála (ha ettől eltérő, később finomítható)
            ratings.append(
                RatingSummary(
                    dimension=dim.name,
                    self_score=None,
                    others_score=float(avg_score),
                    scale_min=1,
                    scale_max=5,
                )
            )

        return ratings

    def _build_text_feedbacks(self, eval_qs) -> List[TextFeedback]:
        """
        Minden nem üres szöveges válasz összegyűjtése.
        """

        answers = (
            Answer.objects.filter(
                evaluation__in=eval_qs,
                question__question_type="text",
            )
            .exclude(value_text__isnull=True)
            .exclude(value_text__exact="")
            .select_related("evaluation")
        )

        feedbacks: List[TextFeedback] = []

        for ans in answers:
            q_type = ans.evaluation.questionnaire_type
            if q_type == "student_to_teacher":
                source = "student"
            elif q_type == "teacher_to_student":
                source = "teacher"
            else:
                source = "other"

            feedbacks.append(
                TextFeedback(
                    source_type=source,
                    text=ans.value_text.strip(),
                )
            )

        return feedbacks

    def _build_objective_data(self, eval_qs) -> List[ObjectiveData]:
        """
        Evaluation-ökhöz kapcsolt objektív mutatók összegyűjtése.
        """

        metrics = ObjectiveMetric.objects.filter(evaluation__in=eval_qs)

        objs: List[ObjectiveData] = []
        for m in metrics:
            objs.append(ObjectiveData(label=m.label, value=m.value))

        return objs

    # ---------- Nyers EvaluationInput → GPT-5.1 hívás ----------

    def generate_feedback(self, data: EvaluationInput) -> str:
        """
        Megkap egy EvaluationInput-ot, felépít egy promptot, és meghívja a modellt.
        """

        prompt = self._build_prompt(data)

        try:
            response = self.client.responses.create(
                model=self.model,
                # Rövid szerep-leírás
                instructions=(
                    "Te egy pedagógiai értékelésben segítő szakértői asszisztens vagy. "
                    "Feladatod, hogy az adatok alapján valósághű, kiegyensúlyozott és "
                    "fejlesztő jellegű visszajelzést adj a tanárnak."
                ),
                input=prompt,
                max_output_tokens=1200,
            )
        except openai.RateLimitError:
            # Ha elfogy a kredit / túl sok kérés, ne dobjuk szét az appot
            return (
                "Jelenleg nem tudok automatikus szöveges kiértékelést készíteni, "
                "mert az AI-szolgáltatás elérte a használati korlátot (RateLimitError)."
            )
        except openai.APIError as e:
            return (
                "Hiba történt az AI-szolgáltatás hívása közben, ezért most nem tudok "
                f"részletes szöveges értékelést adni. (APIError: {e})"
            )

        # Egyszerű szöveges kinyerés (Responses API)
        # lásd: https://platform.openai.com/docs/guides/text
        try:
            return response.output_text
        except AttributeError:
            # Biztonsági fallback, ha változik az SDK
            return str(response)

    def _build_prompt(self, data: EvaluationInput) -> str:
        """
        A modellnek küldött, ember-olvasható prompt szöveg.
        Magyarul fogalmazunk, mert a cél a magyar nyelvű értékelés.
        """

        lines: List[str] = []

        lines.append(
            f"Az alábbi adatok egy tanár értékeléséből származnak.\n"
            f"Értékelt személy: {data.evaluated_name} "
            f"(szerep: {data.evaluated_role}, kontextus: {data.context}).\n"
            "Készíts fejlesztő jellegű, őszinte, de támogató visszajelzést."
        )

        # ---------- Numerikus rész ----------
        lines.append("\n[NUMERIKUS (LIKERT-SKÁLÁS) EREDMÉNYEK]\n")

        if not data.ratings:
            lines.append("Nincsenek elérhető skálás (1–5) értékelések.\n")
        else:
            lines.append("Minden dimenzió 1–5-ös skálán lett értékelve.\n")
            for r in data.ratings:
                lines.append(
                    f"- Dimenzió: {r.dimension} | "
                    f"Diákok átlagos értékelése: {r.others_score:.2f} "
                    f"(skála: {r.scale_min}–{r.scale_max})"
                    + (
                        f" | Önértékelés: {r.self_score:.2f}"
                        if r.self_score is not None
                        else ""
                    )
                )

        # ---------- Szöveges rész ----------
        lines.append("\n[NYITOTT, SZÖVEGES VISSZAJELZÉSEK]\n")

        if not data.texts:
            lines.append(
                "Nincsenek szöveges visszajelzések (kommentek). "
                "Kérlek, ezt is vedd figyelembe: kevesebb a kvalitatív információ.\n"
            )
        else:
            lines.append(
                "Az alábbiak a diákok (vagy más értékelők) szöveges visszajelzései "
                "változtatás nélkül:\n"
            )
            for i, t in enumerate(data.texts, start=1):
                src = {
                    "student": "Diák",
                    "teacher": "Tanár",
                    "other": "Egyéb forrás",
                }.get(t.source_type, "Ismeretlen forrás")
                lines.append(f"{i}. [{src}] {t.text}")

        # ---------- Objektív mutatók ----------
        lines.append("\n[OBJEKTÍV MUTATÓK]\n")

        if not data.objective_data:
            lines.append(
                "Nincsenek kapcsolódó objektív mutatók (pl. jegyátlag, bukási arány). "
                "Az értékelés így főként a diákok szubjektív visszajelzéseire támaszkodik.\n"
            )
        else:
            lines.append(
                "Az alábbi objektív adatok kapcsolódnak a tanár teljesítményéhez:\n"
            )
            for obj in data.objective_data:
                lines.append(f"- {obj.label}: {obj.value}")

        # ---------- Feladat explicit megfogalmazása ----------
        lines.append(
            "\n[Feladatod]\n"
            "1. Foglald össze röviden a tanár fő erősségeit.\n"
            "2. Nevezd meg a legfontosabb fejlesztendő területeket.\n"
            '3. Adj legfeljebb 5 konkrét, gyakorlati javaslatot ("Mit tegyen másképp?").\n'
            "4. Ha az adatok kevésnek tűnnek, ezt is jelezd, és óvatosan fogalmazz.\n"
            "5. Ne találj ki számokat vagy tényeket, csak az adatokból következtess.\n"
            "6. Magyarul válaszolj, tegezve, de tisztelettel.\n"
        )

        return "\n".join(lines)
