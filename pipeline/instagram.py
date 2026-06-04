"""Gera legendas de Instagram para os 6 cortes em uma única chamada OpenAI."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable


@dataclass
class InstagramPost:
    idx: int
    hook: str
    caption: str
    cta: str
    hashtags: list[str]


SYSTEM_PROMPT = (
    "Você é o gerente de redes sociais de uma igreja batista (IBB). Para cada "
    "corte de palestra recebido, escreve a legenda do post de Instagram com:\n"
    "- hook: 1 linha forte de até 80 caracteres, que prende antes do \"...mais\".\n"
    "- caption: 3 a 6 parágrafos curtos em PT-BR, voz reflexiva, conecta a ideia "
    "do corte ao cotidiano do leitor. Sem jargão excessivo. NÃO INVENTE versículos, "
    "referências bíblicas ou citações que não estejam no texto fonte.\n"
    "- cta: chamada para Salvar, Compartilhar ou Comentar (varia ligeiramente "
    "entre posts; emoji opcional).\n"
    "- hashtags: 10 a 15 em PT-BR, mistura de amplas (#fe, #palavradedeus, "
    "#devocional, #cristao) e nichadas (#ibb, #igrejabatista). Sem hashtags "
    "genéricas de marketing como #instagood ou #love.\n"
    "Responda APENAS com JSON conforme o schema solicitado."
)


JSON_SCHEMA = {
    "name": "instagram_posts",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "posts": {
                "type": "array",
                "minItems": 6,
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "idx": {"type": "integer"},
                        "hook": {"type": "string"},
                        "caption": {"type": "string"},
                        "cta": {"type": "string"},
                        "hashtags": {
                            "type": "array",
                            "minItems": 10,
                            "maxItems": 15,
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["idx", "hook", "caption", "cta", "hashtags"],
                },
            },
        },
        "required": ["posts"],
    },
    "strict": True,
}


def _build_user_message(cuts: list[dict]) -> str:
    payload = [
        {
            "idx": c["idx"],
            "title": c.get("title"),
            "rationale": c.get("rationale"),
            "text": c.get("text", ""),
        }
        for c in cuts
    ]
    return (
        "Aqui estão os 6 cortes do vídeo. Para cada um, gere um post para o feed do "
        "Instagram seguindo o schema. Use o `text` (transcrição literal do trecho) "
        "como base; `title` e `rationale` ajudam a entender o tema.\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )


def _normalize_hashtags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for t in tags:
        t = t.strip()
        if not t:
            continue
        if not t.startswith("#"):
            t = "#" + t.lstrip("#")
        t = re.sub(r"\s+", "", t)
        key = t.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
        if len(out) == 15:
            break
    return out


def _validate(raw: dict) -> list[InstagramPost] | None:
    posts = raw.get("posts")
    if not isinstance(posts, list) or len(posts) != 6:
        return None
    result: list[InstagramPost] = []
    seen_idx: set[int] = set()
    for p in posts:
        if not isinstance(p, dict):
            return None
        try:
            idx = int(p["idx"])
        except (KeyError, TypeError, ValueError):
            return None
        if idx in seen_idx or not (1 <= idx <= 6):
            return None
        seen_idx.add(idx)
        hook = str(p.get("hook", "")).strip()[:80]
        caption = str(p.get("caption", "")).strip()
        cta = str(p.get("cta", "")).strip()
        if not (hook and caption and cta):
            return None
        hashtags = _normalize_hashtags(p.get("hashtags") or [])
        if len(hashtags) < 5:  # tolerância mínima
            return None
        result.append(InstagramPost(idx=idx, hook=hook, caption=caption, cta=cta, hashtags=hashtags))
    result.sort(key=lambda x: x.idx)
    return result


def generate(
    cuts: list[dict],
    on_event: Callable[[dict], None],
    *,
    model: str | None = None,
) -> list[InstagramPost] | None:
    """Retorna lista de 6 posts ou None em caso de falha (não levanta)."""
    if not os.environ.get("OPENAI_API_KEY"):
        on_event({"type": "log", "stage": "instagram", "message": "Pulando — OPENAI_API_KEY ausente"})
        return None
    if os.environ.get("DISABLE_INSTAGRAM"):
        on_event({"type": "log", "stage": "instagram", "message": "Pulando — DISABLE_INSTAGRAM=1"})
        return None
    if len(cuts) != 6:
        on_event({"type": "log", "stage": "instagram", "message": f"Pulando — esperava 6 cortes, vieram {len(cuts)}"})
        return None

    from openai import OpenAI

    client = OpenAI(timeout=30.0)
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    user_msg = _build_user_message(cuts)

    on_event({"type": "progress", "stage": "instagram", "fraction": 0.1})
    last_error: Exception | None = None
    for attempt, temperature in enumerate((0.7, 0.0), start=1):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_schema", "json_schema": JSON_SCHEMA},
                max_tokens=4096,
            )
            on_event({"type": "progress", "stage": "instagram", "fraction": 0.7})
            text = (resp.choices[0].message.content or "").strip()
            raw = json.loads(text)
            posts = _validate(raw)
            if posts is None:
                raise ValueError("validation_failed")
            usage = resp.usage
            if usage:
                on_event({"type": "log", "stage": "instagram", "message": f"OpenAI {model}: {usage.prompt_tokens} in / {usage.completion_tokens} out"})
            on_event({"type": "progress", "stage": "instagram", "fraction": 1.0})
            return posts
        except Exception as e:
            last_error = e
            on_event({"type": "log", "stage": "instagram", "message": f"tentativa {attempt} falhou: {type(e).__name__}: {e}"})
            continue
    on_event({"type": "log", "stage": "instagram", "message": f"Falha definitiva: {type(last_error).__name__}: {last_error}"})
    return None


def _format_txt(post: InstagramPost) -> str:
    return (
        f"{post.hook}\n\n"
        f"{post.caption}\n\n"
        f"{post.cta}\n\n"
        + " ".join(post.hashtags)
        + "\n"
    )


def write_files(posts: list[InstagramPost], cuts: list[dict], out_dir: str) -> None:
    out = Path(out_dir)
    cuts_by_idx = {c["idx"]: c for c in cuts}

    # Per-cut .txt (copy-paste)
    for p in posts:
        (out / f"corte-{p.idx:02d}-instagram.txt").write_text(_format_txt(p), encoding="utf-8")

    # Aggregated .md (human review)
    lines: list[str] = [f"# Instagram — {out.name}\n"]
    for p in posts:
        c = cuts_by_idx.get(p.idx, {})
        title = c.get("title", f"Corte {p.idx}")
        rationale = c.get("rationale")
        lines.append(f"## {p.idx}. {title}")
        if rationale:
            lines.append(f"_{rationale}_\n")
        lines.append(f"**HOOK:** {p.hook}\n")
        lines.append(p.caption + "\n")
        lines.append(f"_{p.cta}_\n")
        lines.append("```\n" + " ".join(p.hashtags) + "\n```\n")
        lines.append("---\n")
    (out / "instagram.md").write_text("\n".join(lines), encoding="utf-8")


def post_to_dict(p: InstagramPost) -> dict:
    return asdict(p)
