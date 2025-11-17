# engine.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional, Any
import os

from openai import OpenAI


# ----------- Adatmodellek (nem Django modellek, csak átmeneti struktúrák) -----------

# Egy dimenzió összesített pontszámai (pl. "Kommunikáció", "Fegyelmezettség")
@dataclass
class RatingSummary:
    dimension: str                       # pl. "Kommunikáció"
    self_score: Optional[float] = None   # önértékelés átlaga
    others_score: Optional[float] = None # mások értékelésének átlaga
    scale_min: int = 1                   # skála alsó határ (pl. 1)
    scale_max: int = 5                   # skála felső határ (pl. 5)


# Nyitott kérdésekre adott szöveges válaszok
@dataclass
class TextFeedback:
    source_type: Literal["student", "teacher", "self", "peer", "other"]
    question_label: str    # pl. "Mi az, amit XY különösen jól csinál?"
    content: str           # maga a szöveges válasz


# Opcionális "objektív" adatok (jegyek, hiányzások, stb.)
@dataclass
class ObjectiveData:
    label: str             # pl. "Féléves átlag", "Hiányzások száma"
    value: Any             # érték (szám, string, stb.)


# Az engine bemenete: mindent egyben tartalmaz
@dataclass
class EvaluationInput:
    evaluated_id: int                     # az értékelt személy azonosítója (DB-ből)
    evaluated_name: str                   # az értékelt megjelenített neve
    evaluated_role: Literal["student", "teacher"]
    context: str                          # pl. "2024/25 1. félév, Matematika"
    ratings: List[RatingSummary]
    texts: List[TextFeedback]
    objective_data: List[ObjectiveData]


# ----------- Maga az értékelő engine -----------

class EvaluationEngine:
    """
    Az értékelő motor, ami:
    - megkapja az EvaluationInput-ot,
    - szöveges promptot épít belőle,
    - meghívja a GPT-5.1 Thinking modellt,
    - visszaad egy strukturált, magyar nyelvű visszajelzést.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        reasoning_effort: Literal["none", "low", "medium", "high"] = "medium",
        verbosity: Literal["low", "medium", "high"] = "medium",
        language: Literal["hu", "en"] = "hu",
    ) -> None:
        # Ha nincs külön api_key megadva, az env változóból olvas
        self.client = OpenAI(api_key="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")
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.verbosity = verbosity
        self.language = language

    # ----------------- Külsőleg hívható fő függvény -----------------

    def generate_feedback(self, data: EvaluationInput) -> str:
        """
        Fő "public" függvény:
        - összerakja a promptot
        - meghívja a GPT-5.1 modellt
        - visszaadja a generált szöveges értékelést
        """
        prompt = self._build_prompt(data)

        # OpenAI Responses API használata GPT-5.1 modellel :contentReference[oaicite:1]{index=1}
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            reasoning={"effort": self.reasoning_effort},
            text={"verbosity": self.verbosity},
        )

        # A docs alapján a fő szöveg az output_text-ből olvasható :contentReference[oaicite:2]{index=2}
        return response.output_text

    # ----------------- Belső segédfüggvény: prompt építése -----------------

    def _build_prompt(self, data: EvaluationInput) -> str:
        """
        A nyers adatokból (pontszámok, szövegek) egy jól strukturált,
        magyar nyelvű promptot épít, amit a modell megkap.
        """

        # 1) Fejléc + instrukciók a modellnek
        if self.language == "hu":
            header = f"""
Te egy pedagógiai értékelő asszisztens vagy.
Feladatod, hogy egy tanárról vagy diákról szóló kérdőív eredményeit
alapján készíts:
- rövid összefoglalót az illetőről,
- felsorolást az erősségekről,
- felsorolást a fejlesztendő területekről,
- néhány konkrét, gyakorlatias javaslatot a fejlődésre.

Beszélj közvetlenül az értékelt személyhez ("te" formában),
tárgyilagosan, bántó jelzők nélkül, fejlesztő, támogató hangnemben.
Ne diagnosztizálj, ne használj pszichológiai szakszavakat (pl. "szorongó személyiség").
"""
        else:
            header = f"""
You are an educational feedback assistant.
Your task is to produce:
- a short summary of the person,
- a list of strengths,
- a list of areas for improvement,
- a few concrete, practical suggestions.

Speak directly to the evaluated person ("you"), in a supportive, non-offensive tone.
Do not diagnose or use psychological jargon.
"""

        # 2) Alap meta-információk
        role_text = "tanár" if data.evaluated_role == "teacher" else "diák"

        meta_block = f"""
[ALAPADATOK]
Név: {data.evaluated_name}
Szerep: {role_text}
Kontekstus: {data.context}
"""

        # 3) Pontszámok összefoglalása dimenziónként
        ratings_lines = []
        for r in data.ratings:
            line = f"- Dimenzió: {r.dimension} (skála: {r.scale_min}-{r.scale_max})"
            if r.self_score is not None:
                line += f"\n    • Önértékelés átlaga: {r.self_score:.2f}"
            if r.others_score is not None:
                line += f"\n    • Mások értékelésének átlaga: {r.others_score:.2f}"
            ratings_lines.append(line)

        ratings_block = "[PONTSZÁMOK DIMENZIÓK SZERINT]\n"
        if ratings_lines:
            ratings_block += "\n".join(ratings_lines)
        else:
            ratings_block += "Nincs elérhető pontszám.\n"

        # 4) Szöveges visszajelzések
        texts_lines = []
        for t in data.texts:
            source_label = {
                "student": "diák",
                "teacher": "tanár",
                "self": "önértékelés",
                "peer": "társ",
                "other": "egyéb"
            }.get(t.source_type, t.source_type)

            texts_lines.append(
                f"\n---\nForrás: {source_label}\nKérdés: {t.question_label}\nVálasz: {t.content}"
            )

        texts_block = "[SZÖVEGES VISSZAJELZÉSEK]"
        if texts_lines:
            texts_block += "".join(texts_lines)
        else:
            texts_block += "\nNincs szöveges visszajelzés."

        # 5) Objektív adatok
        obj_lines = []
        for o in data.objective_data:
            obj_lines.append(f"- {o.label}: {o.value}")

        obj_block = "[OBJEKTÍV ADATOK]\n"
        if obj_lines:
            obj_block += "\n".join(obj_lines)
        else:
            obj_block += "Nincs megadott objektív adat.\n"

        # 6) Instrukció, milyen szerkezetben válaszoljon a modell
        if self.language == "hu":
            output_instruction = """
[KÉRT VÁLASZSTRUKTÚRA]

Kérlek, az alábbi szerkezetben válaszolj magyarul:

1. Rövid összefoglaló (3-5 mondat)
2. Erősségeid (felsorolás, 3-7 pont)
3. Fejlesztendő területek (felsorolás, 3-7 pont)
4. Konkrét javaslatok a következő 1-3 hónapra (max. 5 pont),
   mindegyik pont legyen nagyon gyakorlatias, könnyen érthető.
"""
        else:
            output_instruction = """
[REQUIRED OUTPUT STRUCTURE]

Please answer in the following structure:

1. Short summary (3-5 sentences)
2. Strengths (3-7 bullet points)
3. Areas for improvement (3-7 bullet points)
4. Concrete action suggestions for the next 1-3 months (max. 5 bullets).
"""

        # 7) Minden összeillesztése egyetlen input stringgé
        full_prompt = (
            header.strip()
            + "\n\n"
            + meta_block.strip()
            + "\n\n"
            + ratings_block.strip()
            + "\n\n"
            + texts_block.strip()
            + "\n\n"
            + obj_block.strip()
            + "\n\n"
            + output_instruction.strip()
        )

        return full_prompt
