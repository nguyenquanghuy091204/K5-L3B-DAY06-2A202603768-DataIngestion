"""TODO: evaluate retrieved evidence and preserve per-query traces."""
from typing import Any


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """TODO: check source/page and enough gold evidence; keep hit@1 and hit@3 trace.
    Accept any documented alternative gold evidence. Do not infer human grounding
    or chunk coherence labels from exact string match.
    """
    import re
    import unicodedata

    def _norm(s: str) -> str:
        s = unicodedata.normalize("NFC", s or "").lower()
        s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
        s = re.sub(r"[^a-z0-9']+|\s+", " ", s)
        return s.strip()

    gold_source = question.get("gold_source_id")
    gold_pages = question.get("gold_page")
    if not isinstance(gold_pages, list):
        gold_pages = [gold_pages]
    evidences = question.get("evidence_quote", "")
    if not isinstance(evidences, list):
        evidences = [evidences]
    norm_evidences = [_norm(e) for e in evidences if e]
    evaluated_hits = []
    hit_at_1 = False
    hit_at_3 = False
    for rank, h in enumerate(hits[:3], start=1):
        h_text = _norm(h.get("text", ""))
        source_ok = (gold_source is None) or (h.get("document_id") == gold_source) or (h.get("source") == gold_source)
        page_ok = h.get("page") in gold_pages
        evidence_ok = False
        for ev in norm_evidences:
            if not ev:
                continue
            if ev in h_text:
                evidence_ok = True
                break
            tokens = [tok for tok in ev.split() if len(tok) > 3]
            if tokens and sum(1 for tok in tokens if tok in h_text) / len(tokens) >= 0.7:
                evidence_ok = True
                break
        is_hit = bool(source_ok and page_ok and evidence_ok)
        if rank == 1 and is_hit:
            hit_at_1 = True
        if is_hit:
            hit_at_3 = True
        evaluated_hits.append(
            {
                "rank": rank,
                "chunk_id": h.get("chunk_id"),
                "document_id": h.get("document_id"),
                "source": h.get("source"),
                "page": h.get("page"),
                "score": h.get("score"),
                "metadata": h.get("metadata", {}),
                "text": h.get("text", ""),
                "is_hit": is_hit,
            }
        )
    return {
        "id": question.get("id"),
        "split": question.get("split", "dev"),
        "question": question.get("question"),
        "expected_answer": question.get("expected_answer"),
        "gold_source_id": gold_source,
        "gold_page": question.get("gold_page"),
        "evidence_quote": question.get("evidence_quote"),
        "filter": question.get("filter"),
        "hit_at_1": hit_at_1,
        "evidence_hit_at_3": hit_at_3,
        "top_k": evaluated_hits,
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """TODO: aggregate Hit@1 and Evidence Hit@3 by strategy and dev/test split."""
    by_strategy: dict[str, list[dict[str, Any]]] = {}
    for t in traces:
        strat = t.get("strategy", "default")
        by_strategy.setdefault(strat, []).append(t)
    report: dict[str, Any] = {}
    for strat, items in by_strategy.items():
        strat_res: dict[str, Any] = {}
        for split in ("dev", "test", "all"):
            subset = [x for x in items if split == "all" or x.get("split") == split]
            total = len(subset)
            if total == 0:
                continue
            h1 = sum(1 for x in subset if x.get("hit_at_1"))
            h3 = sum(1 for x in subset if x.get("evidence_hit_at_3"))
            strat_res[split] = {
                "count": total,
                "hit_at_1_num": h1,
                "hit_at_1": f"{h1}/{total}",
                "hit_at_1_pct": round(100.0 * h1 / total, 2),
                "evidence_hit_at_3_num": h3,
                "evidence_hit_at_3": f"{h3}/{total}",
                "evidence_hit_at_3_pct": round(100.0 * h3 / total, 2),
            }
        report[strat] = strat_res
    return report