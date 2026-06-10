from __future__ import annotations

import re
from dataclasses import dataclass, field

from .transcribe import Word


SENTENCE_END = re.compile(r"[.!?…]$")
PT_STOPWORDS = {
    "a", "o", "e", "de", "do", "da", "dos", "das", "que", "para", "por",
    "com", "se", "em", "no", "na", "nos", "nas", "um", "uma", "uns",
    "umas", "como", "mas", "ou", "ao", "à", "às", "aos", "é", "foi",
    "ser", "está", "estão", "tem", "ter", "nós", "vós", "eles", "elas",
    "ele", "ela", "isso", "isto", "aquilo", "este", "esta", "esse", "essa",
    "meu", "minha", "seu", "sua", "nosso", "nossa", "muito", "muita",
    "também", "já", "vai", "vamos", "porque", "quando", "onde", "qual",
    "quem", "todo", "toda", "todos", "todas", "mais", "menos", "só",
    "ainda", "depois", "antes", "sobre", "sem",
}


@dataclass
class Candidate:
    id: int
    start: float
    end: float
    text: str
    strong_start: bool
    strong_end: bool


def _is_strong_end(word: Word) -> bool:
    return bool(SENTENCE_END.search(word.text))


def _gather_boundaries(words: list[Word], min_pause: float) -> list[tuple[int, bool]]:
    """Return list of (word_index_after_boundary, strong_flag).
    Index 0 is always a boundary (beginning). For every gap >= min_pause we record
    the index of the word that *starts* the new region.
    """
    boundaries: list[tuple[int, bool]] = [(0, True)]
    for i in range(1, len(words)):
        gap = words[i].start - words[i - 1].end
        if gap >= min_pause:
            strong = _is_strong_end(words[i - 1])
            boundaries.append((i, strong))
    boundaries.append((len(words), True))
    return boundaries


def gather_candidates(
    words: list[Word],
    *,
    target_min: float = 60.0,
    target_max: float = 180.0,
    min_pause: float = 0.7,
    max_candidates: int = 50,
) -> list[Candidate]:
    if not words:
        return []

    boundaries = _gather_boundaries(words, min_pause)
    raw: list[Candidate] = []
    bid = 0

    for si, (start_idx, start_strong) in enumerate(boundaries[:-1]):
        # Collect ALL strong endpoints within [target_min, target_max] for this start.
        # Multiple endpoints per start let the LLM pick the one with the best narrative arc.
        for ei in range(si + 1, len(boundaries)):
            end_idx, end_strong = boundaries[ei]
            if end_idx == start_idx:
                continue
            dur = words[end_idx - 1].end - words[start_idx].start
            if dur < target_min:
                continue
            if dur > target_max:
                break
            if not end_strong:
                continue
            text = " ".join(w.text for w in words[start_idx:end_idx]).strip()
            bid += 1
            raw.append(Candidate(
                id=bid,
                start=words[start_idx].start,
                end=words[end_idx - 1].end,
                text=text,
                strong_start=start_strong,
                strong_end=end_strong,
            ))

    if not raw:
        return []

    # Distribute across 6 bins, up to ceil(max_candidates/6) per bin.
    total_span = max(raw, key=lambda c: c.end).end - min(raw, key=lambda c: c.start).start
    bin_size = total_span / 6 if total_span > 0 else 1.0
    base = min(raw, key=lambda c: c.start).start
    per_bin = max(1, -(-max_candidates // 6))  # ceiling division

    bins: dict[int, list[Candidate]] = {}
    for c in raw:
        idx = min(5, int((c.start - base) / bin_size))
        bins.setdefault(idx, []).append(c)

    # Prefer strong-start candidates in each bin.
    selected: list[Candidate] = []
    for idx in range(6):
        bucket = sorted(bins.get(idx, []), key=lambda c: (not c.strong_start, c.start))[:per_bin]
        selected.extend(bucket)

    if len(selected) > max_candidates:
        step = len(selected) / max_candidates
        selected = [selected[int(i * step)] for i in range(max_candidates)]

    # Renumber ids 1..N after final pruning.
    for new_id, c in enumerate(selected, start=1):
        c.id = new_id
    return selected


@dataclass
class HeuristicCut:
    idx: int
    start: float
    end: float
    slug: str
    title: str
    rationale: str | None = None


def _slug_from_text(text: str) -> str:
    words = [w.lower() for w in re.findall(r"[A-Za-zÀ-ÿ]+", text)]
    keywords = [w for w in words if w not in PT_STOPWORDS and len(w) > 3]
    counts: dict[str, int] = {}
    for w in keywords:
        counts[w] = counts.get(w, 0) + 1
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
    if not top:
        return "corte"
    return "-".join(w for w, _ in top)


def pick_six_heuristic(candidates: list[Candidate]) -> list[HeuristicCut]:
    """Strict fallback: greedy non-overlapping, preferring strong boundaries."""
    if not candidates:
        return []

    strong = [c for c in candidates if c.strong_start and c.strong_end]
    pool = strong if len(strong) >= 6 else candidates
    pool = sorted(pool, key=lambda c: c.start)

    # Greedy: scan in time order, take a pick if it does not overlap previous one.
    picked: list[Candidate] = []
    for c in pool:
        if picked and c.start < picked[-1].end:
            continue
        picked.append(c)
        if len(picked) == 6:
            break

    # If still short, relax by trying ALL candidates (not just strong)
    if len(picked) < 6 and pool is not candidates:
        for c in sorted(candidates, key=lambda x: x.start):
            if any(c.start < p.end and c.end > p.start for p in picked):
                continue
            picked.append(c)
            picked.sort(key=lambda x: x.start)
            if len(picked) == 6:
                break

    picked = sorted(picked, key=lambda c: c.start)[:6]
    cuts: list[HeuristicCut] = []
    for i, c in enumerate(picked, start=1):
        slug = _slug_from_text(c.text)
        title = " ".join(c.text.split()[:6]).rstrip(",.!?…")
        cuts.append(HeuristicCut(
            idx=i,
            start=c.start,
            end=c.end,
            slug=slug or f"corte-{i:02d}",
            title=title or f"Corte {i}",
        ))
    return cuts
