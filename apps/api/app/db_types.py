import array
import uuid

from sqlalchemy import JSON, LargeBinary
from sqlalchemy.types import TypeDecorator


class UUIDList(TypeDecorator):
    """Stores a list[uuid.UUID] as a JSON array of strings.

    Replaces postgresql.ARRAY(UUID) — the only usages in this codebase are
    Python-side membership checks (`x in conflict.requirement_ids`), never
    SQL-level array queries, so round-tripping through JSON loses nothing.
    """

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return [str(v) for v in value]

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return [uuid.UUID(v) for v in value]


class EmbeddingVector(TypeDecorator):
    """Stores a list[float] embedding as a packed float32 binary blob.

    Replaces pgvector's Vector type for SQLite (and any other dialect) —
    no similarity search happens at the SQL level in this codebase, every
    cosine comparison is done in Python after loading the vector, so a
    plain BLOB is sufficient and far more compact than JSON.
    """

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return array.array("f", value).tobytes()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return array.array("f", value).tolist()
