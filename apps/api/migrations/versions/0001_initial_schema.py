"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-16
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute("""
        CREATE TABLE projects (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name        VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            domain      VARCHAR(100),
            created_at  TIMESTAMPTZ DEFAULT NOW(),
            updated_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE documents (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            name            VARCHAR(255) NOT NULL,
            file_type       VARCHAR(10) NOT NULL,
            file_path       TEXT NOT NULL,
            file_size_bytes INTEGER,
            status          VARCHAR(20) DEFAULT 'uploaded',
            error_message   TEXT,
            created_at      TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE document_chunks (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id   UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index   INTEGER NOT NULL,
            content       TEXT NOT NULL,
            section_title VARCHAR(255),
            embedding     vector(768),
            created_at    TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops)")

    op.execute("""
        CREATE TABLE requirements (
            id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id        UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            code              VARCHAR(50) NOT NULL,
            title             VARCHAR(500) NOT NULL,
            description       TEXT,
            req_type          VARCHAR(50) NOT NULL DEFAULT 'functional',
            priority          VARCHAR(20) DEFAULT 'medium',
            status            VARCHAR(20) DEFAULT 'draft',
            is_ambiguous      BOOLEAN DEFAULT FALSE,
            ambiguity_reason  TEXT,
            source_document_id UUID REFERENCES documents(id),
            source_chunk_id   UUID REFERENCES document_chunks(id),
            embedding         vector(768),
            version           INTEGER DEFAULT 1,
            created_at        TIMESTAMPTZ DEFAULT NOW(),
            updated_at        TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (project_id, code)
        )
    """)
    op.execute("CREATE INDEX ON requirements USING hnsw (embedding vector_cosine_ops)")
    op.execute("CREATE INDEX ON requirements (project_id, status)")
    op.execute("CREATE INDEX ON requirements (project_id, req_type)")

    op.execute("""
        CREATE TABLE code_repositories (
            id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id   UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            name         VARCHAR(255) NOT NULL,
            source_type  VARCHAR(20) NOT NULL,
            source_url   TEXT,
            local_path   TEXT,
            status       VARCHAR(20) DEFAULT 'pending',
            scanned_at   TIMESTAMPTZ,
            file_count   INTEGER DEFAULT 0,
            test_count   INTEGER DEFAULT 0,
            created_at   TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE code_files (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            repository_id   UUID NOT NULL REFERENCES code_repositories(id) ON DELETE CASCADE,
            project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            path            TEXT NOT NULL,
            language        VARCHAR(50),
            content_hash    VARCHAR(64),
            summary         TEXT,
            role_detected   TEXT,
            entities        TEXT[],
            constants       JSONB,
            is_test_file    BOOLEAN DEFAULT FALSE,
            line_count      INTEGER,
            embedding       vector(768),
            created_at      TIMESTAMPTZ DEFAULT NOW(),
            updated_at      TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (repository_id, path)
        )
    """)
    op.execute("CREATE INDEX ON code_files USING hnsw (embedding vector_cosine_ops)")
    op.execute("CREATE INDEX ON code_files (project_id, is_test_file)")

    op.execute("""
        CREATE TABLE tickets (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id  UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            external_id VARCHAR(100),
            source      VARCHAR(20),
            title       VARCHAR(500) NOT NULL,
            description TEXT,
            ticket_type VARCHAR(50),
            status      VARCHAR(100),
            url         TEXT,
            embedding   vector(768),
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX ON tickets USING hnsw (embedding vector_cosine_ops)")

    op.execute("""
        CREATE TABLE trace_links (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id       UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            source_type      VARCHAR(20) NOT NULL,
            source_id        UUID NOT NULL,
            target_type      VARCHAR(20) NOT NULL,
            target_id        UUID NOT NULL,
            link_type        VARCHAR(30) DEFAULT 'implements',
            confidence_score DECIMAL(5,2),
            status           VARCHAR(20) DEFAULT 'suggested',
            validation_note  TEXT,
            is_manual        BOOLEAN DEFAULT FALSE,
            created_at       TIMESTAMPTZ DEFAULT NOW(),
            updated_at       TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (source_type, source_id, target_type, target_id)
        )
    """)
    op.execute("CREATE INDEX ON trace_links (project_id, status)")
    op.execute("CREATE INDEX ON trace_links (source_type, source_id)")
    op.execute("CREATE INDEX ON trace_links (target_type, target_id)")

    op.execute("""
        CREATE TABLE analysis_jobs (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id    UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            job_type      VARCHAR(50) NOT NULL,
            status        VARCHAR(20) DEFAULT 'pending',
            progress      INTEGER DEFAULT 0,
            input_data    JSONB,
            result_data   JSONB,
            error_message TEXT,
            created_at    TIMESTAMPTZ DEFAULT NOW(),
            started_at    TIMESTAMPTZ,
            completed_at  TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX ON analysis_jobs (project_id, status)")

    op.execute("""
        CREATE TABLE llm_usage (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id          UUID REFERENCES projects(id) ON DELETE SET NULL,
            job_id              UUID REFERENCES analysis_jobs(id) ON DELETE SET NULL,
            provider            VARCHAR(20) NOT NULL,
            model               VARCHAR(100) NOT NULL,
            operation           VARCHAR(50) NOT NULL,
            input_tokens        INTEGER DEFAULT 0,
            output_tokens       INTEGER DEFAULT 0,
            duration_ms         INTEGER,
            estimated_cost_usd  DECIMAL(10,6) DEFAULT 0,
            created_at          TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX ON llm_usage (project_id, created_at)")

    op.execute("""
        CREATE TABLE detected_conflicts (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id       UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            rule_id          VARCHAR(20),
            severity         VARCHAR(10) DEFAULT 'warning',
            title            VARCHAR(500) NOT NULL,
            description      TEXT,
            requirement_ids  UUID[],
            status           VARCHAR(20) DEFAULT 'open',
            created_at       TIMESTAMPTZ DEFAULT NOW(),
            resolved_at      TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX ON detected_conflicts (project_id, status)")

    op.execute("""
        CREATE TABLE llm_settings (
            id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            provider             VARCHAR(20) NOT NULL DEFAULT 'ollama',
            ollama_base_url      TEXT DEFAULT 'http://ollama:11434',
            ollama_model         VARCHAR(100) DEFAULT 'llama3.1:8b',
            ollama_embed_model   VARCHAR(100) DEFAULT 'nomic-embed-text',
            openai_api_key_hash  TEXT,
            openai_model         VARCHAR(100) DEFAULT 'gpt-4o-mini',
            mistral_api_key_hash TEXT,
            mistral_model        VARCHAR(100) DEFAULT 'mistral-small-latest',
            updated_at           TIMESTAMPTZ DEFAULT NOW()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS llm_settings")
    op.execute("DROP TABLE IF EXISTS detected_conflicts")
    op.execute("DROP TABLE IF EXISTS llm_usage")
    op.execute("DROP TABLE IF EXISTS analysis_jobs")
    op.execute("DROP TABLE IF EXISTS trace_links")
    op.execute("DROP TABLE IF EXISTS tickets")
    op.execute("DROP TABLE IF EXISTS code_files")
    op.execute("DROP TABLE IF EXISTS code_repositories")
    op.execute("DROP TABLE IF EXISTS requirements")
    op.execute("DROP TABLE IF EXISTS document_chunks")
    op.execute("DROP TABLE IF EXISTS documents")
    op.execute("DROP TABLE IF EXISTS projects")
    op.execute("DROP EXTENSION IF EXISTS vector")
