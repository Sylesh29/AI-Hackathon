from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from .repository import MemoryRecord


class Base(DeclarativeBase):
    pass


class MemoryEntryORM(Base):
    __tablename__ = "memory_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signature: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    fix: Mapped[str] = mapped_column(String(2000), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    uses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_used: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SqlAlchemyMemoryRepository:
    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(db_url, future=True)
        self._session_factory = sessionmaker(bind=self.engine, future=True)
        Base.metadata.create_all(self.engine)

    def readiness_check(self) -> tuple[bool, str]:
        try:
            with self.engine.connect() as conn:
                conn.execute(select(1))
            return True, "memory_store_accessible_sqlite"
        except Exception as exc:  # pragma: no cover - defensive
            return False, f"memory_store_unavailable_sqlite: {exc.__class__.__name__}"

    @staticmethod
    def _to_record(entry: MemoryEntryORM) -> MemoryRecord:
        return MemoryRecord(
            signature=entry.signature,
            fix=entry.fix,
            outcome=entry.outcome,
            uses=entry.uses,
            last_used=entry.last_used.isoformat() if entry.last_used else None,
        )

    def find_fix(self, signature: str) -> MemoryRecord | None:
        with self._session_factory() as session:
            row = session.execute(
                select(MemoryEntryORM)
                .where(MemoryEntryORM.signature == signature, MemoryEntryORM.outcome == "success")
                .order_by(MemoryEntryORM.uses.desc(), MemoryEntryORM.id.asc())
            ).scalars().first()

            if row is None:
                return None

            row.uses = int(row.uses) + 1
            row.last_used = datetime.now(tz=timezone.utc)
            session.commit()
            session.refresh(row)
            return self._to_record(row)

    def add_or_update(self, signature: str, fix: str, outcome: str) -> bool:
        with self._session_factory() as session:
            row = session.execute(
                select(MemoryEntryORM).where(
                    MemoryEntryORM.signature == signature,
                    MemoryEntryORM.fix == fix,
                )
            ).scalars().first()

            if row is None:
                row = MemoryEntryORM(
                    signature=signature,
                    fix=fix,
                    outcome=outcome,
                    uses=1,
                    last_used=datetime.now(tz=timezone.utc),
                )
                session.add(row)
                session.commit()
                return True

            row.outcome = outcome
            row.uses = int(row.uses) + 1
            row.last_used = datetime.now(tz=timezone.utc)
            session.commit()
            return False

    def top_entries(self, limit: int = 5) -> list[MemoryRecord]:
        with self._session_factory() as session:
            rows = session.execute(
                select(MemoryEntryORM).order_by(
                    MemoryEntryORM.uses.desc(),
                    MemoryEntryORM.last_used.desc(),
                    MemoryEntryORM.id.asc(),
                )
            ).scalars().all()
        return [self._to_record(row) for row in rows[:limit]]
