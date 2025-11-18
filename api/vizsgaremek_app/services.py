# valahol a services-ben vagy a view-ban

from .models import Evaluation, ObjectiveMetric
from .engine import EvaluationInput, ObjectiveData, RatingSummary, TextFeedback


def build_evaluation_input_for_teacher(teacher, context_str: str) -> EvaluationInput:
    # 1) összes Evaluation, ami a tanárra vonatkozik
    evaluations = Evaluation.objects.filter(
        evaluated=teacher,
        evaluated_role="teacher",
        context=context_str,  # vagy szűrsz félévre, tárgyra stb.
    )

    # 2) itt számolod a RatingSummary-kat a Likert válaszokból (ezt majd külön megírjuk)
    ratings: list[RatingSummary] = [...]

    # 3) szöveges visszajelzések gyűjtése (Answer.value_text-ből)
    texts: list[TextFeedback] = [...]

    # 4) objektív mutatók összegyűjtése az összes Evaluation-höz tartozó ObjectiveMetric-ből
    metrics = ObjectiveMetric.objects.filter(evaluation__in=evaluations)
    objective_data = [
        ObjectiveData(label=m.label, value=m.value)
        for m in metrics
    ]

    return EvaluationInput(
        evaluated_id=teacher.id,
        evaluated_name=teacher.get_full_name() if hasattr(teacher, "get_full_name") else str(teacher),
        evaluated_role="teacher",
        context=context_str,
        ratings=ratings,
        texts=texts,
        objective_data=objective_data,
    )
