"""Suggested pipeline entry point; TODO: implement the orchestration."""


def main() -> None:
    """TODO:
    1. Load the corpus and benchmark; validate at least 30 content pages.
    2. Build strategies A (fixed), B (paragraph) and C (B + metadata filter).
    3. Embed with the same model and store vectors/metadata per strategy.
    4. Run the same dev/test questions and save full top-3 traces.
    5. Report retrieval metrics and prepare samples for manual assessment.
    Follow the five dimensions in ../../BENCHMARK.md.
    """
    import json
    import os
    import time
    from pathlib import Path
    from dotenv import load_dotenv
    from .chunking import by_paragraph, fixed_size
    from .embeddings import MyEmbedder
    from .evaluation import evaluate_query, summarize
    from .ingestion import load_pdf
    from .store import PgVectorStore

    starter_dir = Path(__file__).resolve().parents[1]
    root_dir = starter_dir.parent
    load_dotenv(starter_dir / ".env")
    db_url = os.getenv("DATABASE_URL")
    model_name = os.getenv("EMBEDDING_MODEL") or "sentence-transformers/all-MiniLM-L6-v2"
    if not db_url:
        raise RuntimeError("DATABASE_URL is missing in starter/.env")
    pdf_path = starter_dir / "data" / "art_of_war.pdf"
    benchmark_path = root_dir / "benchmark" / "benchmark.json"
    results_dir = starter_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load corpus & validate >= 30 content pages (Sửa document_id khớp với benchmark.json)
    pages = load_pdf(pdf_path, document_id="art-of-war-1910", source="starter/data/art_of_war.pdf")
    content_pages = [p for p in pages if p.metadata.get("is_content_page")]
    if len(content_pages) < 30:
        raise ValueError(f"Corpus only has {len(content_pages)} content pages; at least 30 required.")
    print(f"Loaded {len(pages)} physical pages ({len(content_pages)} valid content pages).")

    with open(benchmark_path, "r", encoding="utf-8") as f:
        raw_bench = json.load(f)
    # Sửa Lỗi 1: Lấy danh sách câu hỏi từ khóa "questions" nếu file JSON là dict
    questions = raw_bench["questions"] if isinstance(raw_bench, dict) and "questions" in raw_bench else raw_bench
    print(f"Loaded {len(questions)} benchmark questions.")

    # 2 & 3. Initialize real embedder & pgvector store
    embedder = MyEmbedder(model_name=model_name)
    store = PgVectorStore(database_url=db_url, dimensions=embedder.dimensions)
    store.create_schema()
    all_traces = []
    stats = {}
    for strategy in ("A", "B", "C"):
        t0 = time.time()
        chunks = []
        for p in content_pages:
            if strategy == "A":
                chunks.extend(fixed_size(p, size=450, overlap=50))
            else:
                chunks.extend(by_paragraph(p, max_size=600))
        vectors = embedder.embed_documents([c.text for c in chunks])
        store.upsert(strategy=strategy, chunks=chunks, vectors=vectors)
        # Verify idempotent re-ingestion does not duplicate rows
        store.upsert(strategy=strategy, chunks=chunks, vectors=vectors)
        elapsed = round(time.time() - t0, 2)
        # 4. Run dev/test benchmark questions & save top-3 traces
        strat_traces = []
        for q in questions:
            q_vec = embedder.embed_query(q["question"])
            q_filter = q.get("filter") if strategy == "C" else None
            hits = store.search(strategy=strategy, query_vector=q_vec, top_k=3, filters=q_filter)
            ev = evaluate_query(q, hits)
            ev["strategy"] = strategy
            strat_traces.append(ev)
            all_traces.append(ev)
        with open(results_dir / f"traces_{strategy}.json", "w", encoding="utf-8") as f:
            json.dump(strat_traces, f, ensure_ascii=False, indent=2)
        stats[strategy] = {
            "chunk_count": len(chunks),
            "avg_chunk_chars": round(sum(len(c.text) for c in chunks) / max(len(chunks), 1), 1),
            "total_chars": sum(len(c.text) for c in chunks),
            "ingest_seconds": elapsed,
            "cost_usd": 0.0,
        }
    # 5. Summarize metrics & save outputs
    summary = summarize(all_traces)
    final_output = {"model": model_name, "dimensions": embedder.dimensions, "stats": stats, "summary": summary}
    with open(results_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    print(json.dumps(final_output, indent=2))


if __name__ == "__main__":
    main()