"""TODO: store and search vectors using PostgreSQL + pgvector."""
from typing import Any
from .models import Chunk


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        """TODO: retain connection settings; validate model dimensions."""
        if not database_url:
            raise ValueError("database_url is required")
        if dimensions <= 0:
            raise ValueError("dimensions must be a positive integer")
        self.database_url = database_url
        self.dimensions = dimensions

    def create_schema(self) -> None:
        """TODO: create table with vector column and source/page/filter metadata."""
        import psycopg
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS rag_chunks (
                        strategy TEXT NOT NULL,
                        chunk_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        source TEXT NOT NULL,
                        page INTEGER NOT NULL,
                        text TEXT NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        embedding vector({self.dimensions}) NOT NULL,
                        PRIMARY KEY (strategy, chunk_id)
                    );
                    CREATE INDEX IF NOT EXISTS idx_rag_chunks_strategy ON rag_chunks (strategy);
                    """
                )
            conn.commit()

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """TODO: validate lengths/dimensions and write stable IDs without duplicates.
        When re-ingesting changed source documents, remove obsolete chunks too.
        """
        import json
        import psycopg
        if len(chunks) != len(vectors):
            raise ValueError("Number of chunks and vectors must match")
        for v in vectors:
            if len(v) != self.dimensions:
                raise ValueError(f"Vector dimension {len(v)} != store dimension {self.dimensions}")
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM rag_chunks WHERE strategy = %s;",
                    (strategy,),
                )
                for chunk, vec in zip(chunks, vectors):
                    vec_str = "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"
                    cur.execute(
                        """
                        INSERT INTO rag_chunks (strategy, chunk_id, document_id, source, page, text, metadata, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::vector)
                        ON CONFLICT (strategy, chunk_id) DO UPDATE SET
                            document_id = EXCLUDED.document_id,
                            source = EXCLUDED.source,
                            page = EXCLUDED.page,
                            text = EXCLUDED.text,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding;
                        """,
                        (
                            strategy,
                            chunk.chunk_id,
                            chunk.document_id,
                            chunk.source,
                            chunk.page,
                            chunk.text,
                            json.dumps(chunk.metadata),
                            vec_str,
                        ),
                    )
            conn.commit()

    def search(self, strategy: str, query_vector: list[float], top_k: int = 3,
               filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """TODO: filter permitted metadata in SQL, rank by cosine distance, return top-k.
        Return chunk ID, text, score and metadata. Parameterize user-supplied values.
        """
        import json
        import psycopg
        if len(query_vector) != self.dimensions:
            raise ValueError("Query vector dimension mismatch")
        allowed_keys = {"section", "chapter", "document_type", "year", "category"}
        vec_str = "[" + ",".join(f"{float(x):.8f}" for x in query_vector) + "]"
        sql = """
            SELECT chunk_id, document_id, source, page, text, metadata,
                   1.0 - (embedding <=> %s::vector) AS score
            FROM rag_chunks
            WHERE strategy = %s
        """
        params: list[Any] = [vec_str, strategy]
        if filters:
            for k, val in filters.items():
                if k not in allowed_keys:
                    raise ValueError(f"Filter key '{k}' is not in permitted metadata keys")
                sql += " AND metadata->>%s = %s"
                params.extend([k, str(val)])
        sql += " ORDER BY embedding <=> %s::vector ASC LIMIT %s;"
        params.extend([vec_str, top_k])
        hits: list[dict[str, Any]] = []
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                for row in cur.fetchall():
                    meta = row[5] if isinstance(row[5], dict) else json.loads(row[5])
                    hits.append(
                        {
                            "chunk_id": row[0],
                            "document_id": row[1],
                            "source": row[2],
                            "page": row[3],
                            "text": row[4],
                            "metadata": meta,
                            "score": round(float(row[6]), 4),
                        }
                    )
        return hits