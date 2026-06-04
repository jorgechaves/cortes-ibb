from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Callable

from .selector import Candidate, HeuristicCut, _slug_from_text


class SemanticSelectionFailure(Exception):
    pass


@dataclass
class SemanticChoice:
    id: int
    title: str
    rationale: str
    slug: str


SYSTEM_PROMPT = (
    "Você é um editor de redes sociais. Recebe trechos candidatos extraídos de "
    "uma palestra e escolhe os 6 melhores para clipes curtos. Critérios, em "
    "ordem: (a) ideia completa e auto-contida; (b) abertura clara que prende "
    "atenção; (c) fechamento conclusivo; (d) valor isolado quando assistido "
    "fora de contexto; (e) diversidade temática entre os 6. Responda APENAS "
    "com JSON válido no formato pedido, sem texto adicional."
)


JSON_SCHEMA = {
    "name": "selections",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "selections": {
                "type": "array",
                "minItems": 6,
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "rationale": {"type": "string"},
                        "slug": {"type": "string"},
                    },
                    "required": ["id", "title", "rationale", "slug"],
                },
            }
        },
        "required": ["selections"],
    },
    "strict": True,
}


def _build_user_message(candidates: list[Candidate], video_summary: str | None) -> str:
    payload = [
        {"id": c.id, "start": round(c.start, 2), "end": round(c.end, 2), "text": c.text}
        for c in candidates
    ]
    prelude = (
        f"Vídeo: ~{candidates[-1].end:.0f} segundos.\n"
        + (f"Resumo: {video_summary}\n" if video_summary else "")
        + f"Candidatos ({len(candidates)}):\n"
    )
    return (
        prelude
        + json.dumps(payload, ensure_ascii=False)
        + "\n\nEscolha exatamente 6 candidatos referenciando o `id` de cada um. "
        + "Para cada escolha, retorne `title` (até 8 palavras), `rationale` "
        + "(1 frase justificando) e `slug` (kebab-case, 2-3 palavras)."
    )


def _validate_selections(
    raw: dict, candidates_by_id: dict[int, Candidate]
) -> list[SemanticChoice]:
    sels = raw.get("selections")
    if not isinstance(sels, list) or len(sels) != 6:
        raise SemanticSelectionFailure(f"expected 6 selections, got {len(sels) if isinstance(sels, list) else 'none'}")
    seen: set[int] = set()
    out: list[SemanticChoice] = []
    for s in sels:
        if not isinstance(s, dict):
            raise SemanticSelectionFailure("selection entry not an object")
        try:
            cid = int(s["id"])
        except (KeyError, TypeError, ValueError) as e:
            raise SemanticSelectionFailure(f"invalid id: {e}") from e
        if cid in seen:
            raise SemanticSelectionFailure(f"duplicate id {cid}")
        if cid not in candidates_by_id:
            raise SemanticSelectionFailure(f"id {cid} not in candidates")
        seen.add(cid)
        title = str(s.get("title", "")).strip()
        title_words = title.split()
        if len(title_words) > 8:
            title = " ".join(title_words[:8])
        rationale = str(s.get("rationale", "")).strip()[:240]
        slug = str(s.get("slug", "")).strip() or _slug_from_text(candidates_by_id[cid].text)
        slug = re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-") or f"corte-{cid}"
        out.append(SemanticChoice(id=cid, title=title, rationale=rationale, slug=slug))
    return out


def choose(
    candidates: list[Candidate],
    on_event: Callable[[dict], None],
    *,
    model: str | None = None,
    video_summary: str | None = None,
) -> list[HeuristicCut]:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SemanticSelectionFailure("missing_api_key")
    if os.environ.get("DISABLE_SEMANTIC_SELECTION"):
        raise SemanticSelectionFailure("disabled_by_env")
    if len(candidates) < 6:
        raise SemanticSelectionFailure(f"not_enough_candidates ({len(candidates)})")

    from openai import OpenAI  # lazy

    client = OpenAI(timeout=30.0)
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    on_event({"type": "progress", "stage": "select", "fraction": 0.1})
    user_msg = _build_user_message(candidates, video_summary)

    last_error: Exception | None = None
    for attempt, temperature in enumerate((0.4, 0.0), start=1):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_schema", "json_schema": JSON_SCHEMA},
                max_tokens=2048,
            )
            on_event({"type": "progress", "stage": "select", "fraction": 0.7})
            text = (resp.choices[0].message.content or "").strip()
            text = _extract_json(text)
            raw = json.loads(text)
            candidates_by_id = {c.id: c for c in candidates}
            sels = _validate_selections(raw, candidates_by_id)
            usage = resp.usage
            if usage:
                on_event({"type": "log", "stage": "select", "message": f"OpenAI {model}: {usage.prompt_tokens} in / {usage.completion_tokens} out"})
            on_event({"type": "progress", "stage": "select", "fraction": 1.0})

            chosen = sorted(
                ((candidates_by_id[s.id], s) for s in sels),
                key=lambda pair: pair[0].start,
            )
            cuts: list[HeuristicCut] = []
            for idx, (cand, sel) in enumerate(chosen, start=1):
                cuts.append(HeuristicCut(
                    idx=idx,
                    start=cand.start,
                    end=cand.end,
                    slug=sel.slug,
                    title=sel.title or " ".join(cand.text.split()[:6]),
                    rationale=sel.rationale or None,
                ))
            return cuts
        except (json.JSONDecodeError, SemanticSelectionFailure, KeyError) as e:
            last_error = e
            on_event({"type": "log", "stage": "select", "message": f"tentativa {attempt} falhou: {e}"})
            continue
        except Exception as e:  # network / API
            last_error = e
            on_event({"type": "log", "stage": "select", "message": f"erro API tentativa {attempt}: {type(e).__name__}: {e}"})
            continue

    raise SemanticSelectionFailure(f"api_error: {type(last_error).__name__}: {last_error}")


def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start:end + 1]
    return text
