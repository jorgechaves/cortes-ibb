from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

# ── Colour palette (RGB 0-1) ──────────────────────────────────────────────────
_NAVY = (0.086, 0.141, 0.227)
_GOLD = (0.769, 0.588, 0.227)
_TEAL = (0.290, 0.565, 0.643)
_GRAY_HEADER = (0.533, 0.533, 0.533)
_BODY_TEXT = (0.102, 0.102, 0.102)

# ── Layout constants (points) ─────────────────────────────────────────────────
_BAR_H = 28        # gold horizontal bar height
_VBAR_W = 18       # gold vertical bar width
_ICON_SMALL = 30   # cover icon size
_ICON_BIG = 100    # back-cover icon size
_CONTENT_LEFT = 36 # left edge for cover text (right of vertical bar + gap)

# ── Editor skill paths ────────────────────────────────────────────────────────
_SKILL_PATH = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "editor" / "SKILL.md"

_SKILL_SUFFIX = (
    "\n\n---\n"
    "CONTEXTO ESPECÍFICO (aplique ao texto abaixo):\n"
    "- Edite em português brasileiro.\n"
    "- O texto é a transcrição de um sermão evangélico.\n"
    "- Preserve citações bíblicas literalmente, sem qualquer alteração.\n"
    "- Preserve termos teológicos e expressões de fé.\n"
    "- NÃO resuma, NÃO omita, NÃO reordene o conteúdo.\n"
    "- Ao identificar uma transição temática natural, prefixe o primeiro parágrafo "
    "da nova seção com '## Título Breve' (máximo 5 palavras extraídas do texto que se segue). "
    "Se não houver seções claras, retorne o texto sem marcadores '##'.\n"
    "- Retorne somente o texto editado, sem comentários nem resumo de alterações."
)


def _make_section_rule_class():
    from reportlab.platypus import Flowable

    class SectionRule(Flowable):
        def wrap(self, aW, aH):
            self._rule_w = aW
            return aW, 4

        def draw(self):
            self.canv.setFillColorRGB(*_GOLD)
            self.canv.rect(0, 1, self._rule_w, 0.75, fill=1, stroke=0)

    return SectionRule


_SectionRuleCls = None


def _section_rule():
    global _SectionRuleCls
    if _SectionRuleCls is None:
        _SectionRuleCls = _make_section_rule_class()
    return _SectionRuleCls()


def _edit_chunk_with_claude(chunk: str, system_prompt: str, model: str, client) -> str:
    """Send one chunk to Claude for editing. Raises on error."""
    msg = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": chunk}],
    )
    return msg.content[0].text.strip()


def _edit_chunk_with_openai(chunk: str, system_prompt: str, model: str, client) -> str:
    """Send one chunk to OpenAI for editing. Raises on error."""
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": chunk},
        ],
    )
    return resp.choices[0].message.content.strip()


_OPENAI_SYSTEM = (
    "Você é um editor profissional de português brasileiro especializado em textos de pregação e sermão. "
    "Corrija ortografia, acentuação, concordância. Elimine redundâncias, converta voz passiva para ativa, "
    "fortaleça verbos fracos, melhore coesão entre parágrafos. "
    "Preserve citações bíblicas literalmente e termos teológicos. "
    "NÃO resuma, NÃO omita, NÃO reordene. "
    "Ao identificar transição temática, prefixe com '## Título Breve' (máx 5 palavras do texto que se segue). "
    "Retorne somente o texto editado, sem comentários."
)


def edit_text(text: str, on_event: Callable[[dict], None]) -> str:
    """Edit PT-BR text using the /editor skill via Claude (Anthropic), falling back to OpenAI then original."""
    words = text.split()
    CHUNK = 1500
    chunks = [" ".join(words[i:i + CHUNK]) for i in range(0, len(words), CHUNK)]

    on_event({"type": "log", "stage": "booklet", "message": "Revisando e melhorando o texto em português brasileiro"})

    # ── Level 1: Anthropic + /editor SKILL.md ────────────────────────────────
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key and _SKILL_PATH.exists():
        try:
            import anthropic as _anthropic
            claude_model = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
            client = _anthropic.Anthropic(api_key=anthropic_key)
            skill_content = _SKILL_PATH.read_text(encoding="utf-8")
            # Strip YAML frontmatter (between --- markers)
            lines = skill_content.splitlines()
            if lines and lines[0].strip() == "---":
                end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), None)
                if end:
                    skill_content = "\n".join(lines[end + 1:]).lstrip()
            system_prompt = skill_content + _SKILL_SUFFIX
            on_event({"type": "log", "stage": "booklet", "message": f"Usando skill /editor via Claude ({claude_model})"})
            edited: list[str] = []
            for i, chunk in enumerate(chunks):
                on_event({"type": "progress", "stage": "booklet", "fraction": 0.1 + 0.4 * i / len(chunks)})
                try:
                    edited.append(_edit_chunk_with_claude(chunk, system_prompt, claude_model, client))
                except Exception as e:
                    on_event({"type": "log", "stage": "booklet", "message": f"Claude chunk {i + 1}/{len(chunks)} falhou: {e}"})
                    edited.append(chunk)
            on_event({"type": "log", "stage": "booklet", "message": f"Texto revisado em {len(chunks)} chunk(s) via Claude"})
            return "\n\n".join(edited)
        except Exception as e:
            on_event({"type": "log", "stage": "booklet", "message": f"Anthropic indisponível: {e} — tentando OpenAI"})
    elif anthropic_key and not _SKILL_PATH.exists():
        on_event({"type": "log", "stage": "booklet", "message": f"SKILL.md não encontrado em {_SKILL_PATH} — usando OpenAI como fallback"})

    # ── Level 2: OpenAI fallback ──────────────────────────────────────────────
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            oai_client = OpenAI(api_key=openai_key, timeout=60)
            oai_model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
            on_event({"type": "log", "stage": "booklet", "message": f"Usando OpenAI ({oai_model}) como fallback"})
            edited = []
            for i, chunk in enumerate(chunks):
                on_event({"type": "progress", "stage": "booklet", "fraction": 0.1 + 0.4 * i / len(chunks)})
                try:
                    edited.append(_edit_chunk_with_openai(chunk, _OPENAI_SYSTEM, oai_model, oai_client))
                except Exception as e:
                    on_event({"type": "log", "stage": "booklet", "message": f"OpenAI chunk {i + 1}/{len(chunks)} falhou: {e}"})
                    edited.append(chunk)
            on_event({"type": "log", "stage": "booklet", "message": f"Texto revisado em {len(chunks)} chunk(s) via OpenAI"})
            return "\n\n".join(edited)
        except Exception as e:
            on_event({"type": "log", "stage": "booklet", "message": f"OpenAI indisponível: {e} — usando texto original"})

    # ── Level 3: original text ────────────────────────────────────────────────
    on_event({"type": "log", "stage": "booklet", "message": "Nenhuma API configurada — usando texto original"})
    return text


def _extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("##"):
            for sep in ('.', '!', '?', ',', ';'):
                idx = line.find(sep)
                if idx > 10:
                    return line[:idx]
            return line[:80]
    return fallback


def _parse_story(text: str, body_style, section_style) -> list:
    """Convert corrected text into a ReportLab story (list of flowables)."""
    from reportlab.platypus import Paragraph

    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    if not blocks:
        blocks = [text.strip()] if text.strip() else ["(sem conteúdo)"]

    story = []
    for block in blocks:
        if block.startswith("## "):
            heading = block[3:].strip()
            story.append(Paragraph(heading, section_style))
            story.append(_section_rule())
        else:
            story.append(Paragraph(block, body_style))
    return story


def _draw_bars(c, page_w: float, page_h: float) -> None:
    """Draw the three gold bars (top, bottom, left) common to cover and back cover."""
    c.setFillColorRGB(*_GOLD)
    c.rect(0, page_h - _BAR_H, page_w, _BAR_H, fill=1, stroke=0)   # top bar
    c.rect(0, 0, page_w, _BAR_H, fill=1, stroke=0)                  # bottom bar
    c.rect(0, _BAR_H, _VBAR_W, page_h - 2 * _BAR_H, fill=1, stroke=0)  # left bar


def _word_wrap_lines(c, text: str, font: str, size: float, max_w: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        candidate = (cur + " " + w).strip()
        if c.stringWidth(candidate, font, size) <= max_w:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text[:60]]


def generate_booklet(
    job_dir: str,
    icon_path: str,
    out_path: str,
    on_event: Callable[[dict], None],
) -> str:
    """Generate an A5 PDF booklet from transcript.txt following modelo_livreto.pdf layout."""
    from reportlab.lib.pagesizes import A5
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib.colors import Color
    from reportlab.platypus import (
        BaseDocTemplate, PageTemplate, Frame,
        Paragraph, Spacer, PageBreak, NextPageTemplate,
    )

    transcript_path = Path(job_dir) / "transcript.txt"
    text = transcript_path.read_text(encoding="utf-8")
    job_id = Path(job_dir).name

    on_event({"type": "stage", "stage": "booklet", "message": "Revisando e melhorando o texto"})
    on_event({"type": "progress", "stage": "booklet", "fraction": 0.05})
    corrected = edit_text(text, on_event)

    title = _extract_title(corrected or text, job_id)
    on_event({"type": "log", "stage": "booklet", "message": f"Título: {title}"})
    on_event({"type": "stage", "stage": "booklet", "message": "Montando PDF A5"})
    on_event({"type": "progress", "stage": "booklet", "fraction": 0.55})

    page_w, page_h = A5
    margin = 15 * mm
    icon = str(icon_path)

    # ── Cover page callback ───────────────────────────────────────────────────
    def on_cover(c, doc):
        c.saveState()

        # Navy background
        c.setFillColorRGB(*_NAVY)
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

        # Gold bars
        _draw_bars(c, page_w, page_h)

        # Icon (small, top-left below top bar)
        icon_x = _CONTENT_LEFT
        icon_y = page_h - _BAR_H - _ICON_SMALL - 10
        try:
            c.drawImage(icon, icon_x, icon_y,
                        width=_ICON_SMALL, height=_ICON_SMALL,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

        # "IBB — Igreja Batista Belém" text beside icon
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(*_GOLD)
        c.drawString(
            _CONTENT_LEFT + _ICON_SMALL + 6,
            icon_y + (_ICON_SMALL - 8) / 2,
            "IBB — Igreja Batista Belém",
        )

        # Title (large, white, word-wrapped, left-aligned)
        title_font = "Helvetica-Bold"
        title_size = 36
        title_leading = title_size * 1.2
        max_title_w = page_w - _CONTENT_LEFT - margin
        lines = _word_wrap_lines(c, title, title_font, title_size, max_title_w)

        c.setFont(title_font, title_size)
        c.setFillColorRGB(1, 1, 1)
        title_top_y = page_h * 0.53
        for i, ln in enumerate(lines):
            c.drawString(_CONTENT_LEFT, title_top_y - i * title_leading, ln)

        title_bottom_y = title_top_y - (len(lines) - 1) * title_leading

        # Gold horizontal rule under title
        c.setFillColorRGB(*_GOLD)
        c.rect(
            _CONTENT_LEFT, title_bottom_y - 14,
            page_w - _CONTENT_LEFT - margin, 1.5,
            fill=1, stroke=0,
        )

        # Author at bottom-left
        c.setFont("Helvetica", 12)
        c.setFillColorRGB(1, 1, 1)
        c.drawString(_CONTENT_LEFT, _BAR_H + 16, "Pr. Carlos Chaves")

        c.restoreState()

    # ── Content page callback ─────────────────────────────────────────────────
    def on_content(c, doc):
        page_num = doc.page - 1  # page 1 is the cover
        c.saveState()

        # Header text (title only — no scripture ref for transcripts)
        c.setFont("Helvetica", 8.5)
        c.setFillColorRGB(*_GRAY_HEADER)
        c.drawString(margin, page_h - margin + 10, title)

        # Gold rule immediately below header text
        c.setFillColorRGB(*_GOLD)
        c.rect(margin, page_h - margin + 2, page_w - 2 * margin, 0.75, fill=1, stroke=0)

        # Page number centred at bottom
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(*_GRAY_HEADER)
        c.drawCentredString(page_w / 2, margin - 15, str(page_num))

        c.restoreState()

    # ── Back-cover page callback ──────────────────────────────────────────────
    def on_back_cover(c, doc):
        c.saveState()

        # Navy background
        c.setFillColorRGB(*_NAVY)
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

        # Gold bars (identical to cover)
        _draw_bars(c, page_w, page_h)

        # Icon centred (large)
        ix = (page_w - _ICON_BIG) / 2
        iy = (page_h - _ICON_BIG) / 2
        try:
            c.drawImage(icon, ix, iy,
                        width=_ICON_BIG, height=_ICON_BIG,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

        c.restoreState()

    # ── Page templates ────────────────────────────────────────────────────────
    cover_frame = Frame(margin, margin, page_w - 2 * margin, page_h - 2 * margin, id='cover')
    content_frame = Frame(
        margin, margin + 10,
        page_w - 2 * margin, page_h - 2 * margin - 30,
        id='content',
    )
    back_frame = Frame(margin, margin, page_w - 2 * margin, page_h - 2 * margin, id='back')

    doc = BaseDocTemplate(out_path, pagesize=A5)
    doc.addPageTemplates([
        PageTemplate(id='cover', frames=[cover_frame], onPage=on_cover),
        PageTemplate(id='content', frames=[content_frame], onPage=on_content),
        PageTemplate(id='back_cover', frames=[back_frame], onPage=on_back_cover),
    ])

    # ── Paragraph styles ──────────────────────────────────────────────────────
    body_color = Color(_BODY_TEXT[0], _BODY_TEXT[1], _BODY_TEXT[2])
    teal_color = Color(_TEAL[0], _TEAL[1], _TEAL[2])

    body_style = ParagraphStyle(
        "body",
        fontName="Times-Roman",
        fontSize=11,
        leading=14.3,
        alignment=TA_JUSTIFY,
        textColor=body_color,
        spaceAfter=8,
    )
    section_style = ParagraphStyle(
        "section",
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=teal_color,
        spaceBefore=14,
        spaceAfter=4,
    )

    # ── Story ─────────────────────────────────────────────────────────────────
    content_story = _parse_story(corrected or text, body_style, section_style)

    story = [
        Spacer(1, 1),
        NextPageTemplate('content'),
        PageBreak(),
        *content_story,
        NextPageTemplate('back_cover'),
        PageBreak(),
        Spacer(1, 1),
    ]

    doc.build(story)
    on_event({"type": "progress", "stage": "booklet", "fraction": 0.9})
    on_event({"type": "log", "stage": "booklet", "message": f"PDF gerado: {Path(out_path).name}"})
    return out_path


def upload_booklet_to_drive(pdf_path: str, on_event: Callable[[dict], None]) -> dict | None:
    """Upload booklet PDF to Drive/livros/ subfolder. Returns result dict or None on failure."""
    from . import drive as _drive
    try:
        service = _drive._build_service()
        livros_id = _drive.get_or_create_folder(service, "livros", _drive.TARGET_FOLDER_ID)
        on_event({"type": "log", "stage": "booklet", "message": "Enviando livreto para Drive/livros/"})
        resp = _drive.upload_file(
            service, livros_id, pdf_path, Path(pdf_path).name,
            on_event, 0, 1, mime="application/pdf",
        )
        url = f"https://drive.google.com/file/d/{resp.get('id')}/view"
        on_event({"type": "log", "stage": "booklet", "message": f"Livreto enviado: {url}"})
        return {"id": resp.get("id"), "url": url}
    except _drive.DriveSetupError as e:
        on_event({"type": "log", "stage": "booklet", "message": f"Drive não configurado: {e}"})
        return None
    except Exception as e:
        on_event({"type": "log", "stage": "booklet", "message": f"Upload ao Drive falhou: {e}"})
        return None
