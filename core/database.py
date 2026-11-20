"""Database and storage layer for NyayaSathi using SQLite + SQLAlchemy.

Postgres-ready schema with:
- sessions: id, created_at, last_active_at, language, case_type
- messages: id, session_id, role, content, language, in_scope, created_at
- case_files: session_id, case_data (JSON), updated_at
- summaries: session_id, rolling_summary, covers_up_to_message_id, updated_at

Supports session-based data isolation, rolling summarization, and
a one-click 'Delete my data' wipe. Old sessions older than 30 days are pruned.
"""

from datetime import datetime, timedelta
import json
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from core.config import config
from core.models import CaseFacts

Base = declarative_base()


class SessionRecord(Base):
    """Tracks user sessions, language preference, and case type."""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    language = Column(String(32), default="English")
    case_type = Column(String(32), default="none")  # tenancy | consumer | employment | none

    messages = relationship("MessageRecord", back_populates="session", cascade="all, delete-orphan")
    case_file = relationship("CaseFileRecord", back_populates="session", uselist=False, cascade="all, delete-orphan")
    summary = relationship("SummaryRecord", back_populates="session", uselist=False, cascade="all, delete-orphan")


class MessageRecord(Base):
    """Stores every conversational turn for the session."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    role = Column(String(16), nullable=False)  # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    language = Column(String(32), default="English")
    in_scope = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("SessionRecord", back_populates="messages")


class CaseFileRecord(Base):
    """Stores structured case JSON for legal drafting and context."""
    __tablename__ = "case_files"

    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True)
    case_data = Column(Text, nullable=False)  # JSON representation of CaseFacts
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("SessionRecord", back_populates="case_file")


class SummaryRecord(Base):
    """Stores rolling summary of older messages to conserve token budget."""
    __tablename__ = "summaries"

    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True)
    rolling_summary = Column(Text, default="")
    covers_up_to_message_id = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("SessionRecord", back_populates="summary")


# Initialize Database
DB_PATH = config.data_dir / "nyayasathi.db"
config.data_dir.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_and_migrate_db():
    """Create tables and apply safe schema migrations for SQLite."""
    Base.metadata.create_all(bind=engine)
    # Check for legacy tables or missing columns in sessions table
    with engine.connect() as conn:
        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("sessions")]
        if "last_active_at" not in columns and "last_active" in columns:
            # Legacy column rename or add
            conn.execute(text("ALTER TABLE sessions ADD COLUMN last_active_at DATETIME"))
        if "language" not in columns:
            conn.execute(text("ALTER TABLE sessions ADD COLUMN language VARCHAR(32) DEFAULT 'English'"))
        if "case_type" not in columns:
            conn.execute(text("ALTER TABLE sessions ADD COLUMN case_type VARCHAR(32) DEFAULT 'none'"))
        conn.commit()


init_and_migrate_db()


def init_and_migrate_db():
    """Create tables and apply safe schema migrations for SQLite."""
    with engine.connect() as conn:
        inspector = inspect(engine)
        if "sessions" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("sessions")]
            if "session_id" in columns and "id" not in columns:
                conn.execute(text("ALTER TABLE sessions RENAME COLUMN session_id TO id"))
            if "last_active_at" not in columns and "last_active" in columns:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN last_active_at DATETIME"))
                conn.execute(text("UPDATE sessions SET last_active_at = last_active WHERE last_active_at IS NULL"))
            if "language" not in columns:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN language VARCHAR(32) DEFAULT 'English'"))
            if "case_type" not in columns:
                conn.execute(text("ALTER TABLE sessions ADD COLUMN case_type VARCHAR(32) DEFAULT 'none'"))
        conn.commit()
    Base.metadata.create_all(bind=engine)


init_and_migrate_db()


class DatabaseManager:
    """Helper for session management, conversation turns, case files, and rolling summaries."""

    def __init__(self):
        self.Session = SessionLocal

    def touch_session(
        self,
        session_id: str,
        language: Optional[str] = None,
        case_type: Optional[str] = None,
    ) -> None:
        """Create or update session activity timestamp, language, and case type."""
        with self.Session() as db:
            rec = db.query(SessionRecord).filter_by(id=session_id).first()
            now = datetime.utcnow()
            if not rec:
                rec = SessionRecord(
                    id=session_id,
                    created_at=now,
                    last_active_at=now,
                    language=language or "English",
                    case_type=case_type or "none",
                )
                db.add(rec)
            else:
                rec.last_active_at = now
                if language:
                    rec.language = language
                if case_type and case_type != "none":
                    rec.case_type = case_type
            db.commit()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session record as a dictionary."""
        with self.Session() as db:
            rec = db.query(SessionRecord).filter_by(id=session_id).first()
            if not rec:
                return None
            return {
                "id": rec.id,
                "created_at": rec.created_at,
                "last_active_at": rec.last_active_at,
                "language": rec.language,
                "case_type": rec.case_type,
            }

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        language: str = "English",
        in_scope: bool = True,
    ) -> int:
        """Store a message turn and update session last_active_at timestamp. Returns message id."""
        self.touch_session(session_id, language=language)
        with self.Session() as db:
            msg = MessageRecord(
                session_id=session_id,
                role=role,
                content=content,
                language=language,
                in_scope=in_scope,
                created_at=datetime.utcnow(),
            )
            db.add(msg)
            db.commit()                                                                                                                           
            db.refresh(msg)
            return msg.id

    def add_chat_message(self, session_id: str, sender: str, text: str) -> int:
        """Backward-compatible alias for add_message."""
        return self.add_message(session_id=session_id, role=sender, content=text)

    def get_messages(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve message history for a session in chronological order."""
        with self.Session() as db:
            query = (
                db.query(MessageRecord)
                .filter_by(session_id=session_id)
                .order_by(MessageRecord.id.asc())
            )
            if limit:
                # To get the last N messages in order:
                total = query.count()
                if total > limit:
                    query = query.offset(total - limit)
            recs = query.all()
            return [
                {
                    "id": r.id,
                    "session_id": r.session_id,
                    "role": r.role,
                    "content": r.content,
                    "language": r.language,
                    "in_scope": r.in_scope,
                    "created_at": r.created_at,
                }
                for r in recs
            ]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session record as a dictionary."""
        with self.Session() as db:
            rec = db.query(SessionRecord).filter_by(id=session_id).first()
            if not rec:
                return None
            return {
                "id": rec.id,
                "created_at": rec.created_at,
                "last_active_at": rec.last_active_at,
                "language": rec.language,
                "case_type": rec.case_type,
            }

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        language: str = "English",
        in_scope: bool = True,
    ) -> int:
        """Store a message turn and update session last_active_at timestamp. Returns message id."""
        self.touch_session(session_id, language=language)
        with self.Session() as db:
            msg = MessageRecord(
                session_id=session_id,
                role=role,
                content=content,
                language=language,
                in_scope=in_scope,
                created_at=datetime.utcnow(),
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            return msg.id

    def add_chat_message(self, session_id: str, sender: str, text: str) -> int:
        """Backward-compatible alias for add_message."""
        return self.add_message(session_id=session_id, role=sender, content=text)

    def get_messages(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve message history for a session in chronological order."""
        with self.Session() as db:
            query = (
                db.query(MessageRecord)
                .filter_by(session_id=session_id)
                .order_by(MessageRecord.id.asc())
            )
            if limit:
                # To get the last N messages in order:
                total = query.count()
                if total > limit:
                    query = query.offset(total - limit)
            recs = query.all()
            return [
                {
                    "id": r.id,
                    "session_id": r.session_id,
                    "role": r.role,
                    "content": r.content,
                    "language": r.language,
                    "in_scope": r.in_scope,
                    "created_at": r.created_at,
                }
                for r in recs
            ]

    def get_or_create_case_facts(self, session_id: str) -> CaseFacts:
        """Retrieve stored CaseFacts or create a default blank record."""
        self.touch_session(session_id)
        with self.Session() as db:
            rec = db.query(CaseFileRecord).filter_by(session_id=session_id).first()
            if not rec:
                facts = CaseFacts()
                rec = CaseFileRecord(
                    session_id=session_id,
                    case_data=facts.model_dump_json(),
                    updated_at=datetime.utcnow(),
                )
                db.add(rec)
                db.commit()
                return facts
            else:
                try:
                    data = json.loads(rec.case_data)
                    return CaseFacts(**data)
                except Exception:
                    return CaseFacts()

    def save_case_facts(self, session_id: str, facts: CaseFacts) -> None:
        """Update case facts in the database and update session case_type if known."""
        self.touch_session(session_id, case_type=facts.category if facts.category != "general" else "none")
        with self.Session() as db:
            rec = db.query(CaseFileRecord).filter_by(session_id=session_id).first()
            if not rec:
                rec = CaseFileRecord(
                    session_id=session_id,
                    case_data=facts.model_dump_json(),
                    updated_at=datetime.utcnow(),
                )
                db.add(rec)
            else:
                rec.case_data = facts.model_dump_json()
                rec.updated_at = datetime.utcnow()
            db.commit()

    def get_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve rolling summary and message watermark for a session."""
        with self.Session() as db:
            rec = db.query(SummaryRecord).filter_by(session_id=session_id).first()
            if not rec:
                return None
            return {
                "rolling_summary": rec.rolling_summary,
                "covers_up_to_message_id": rec.covers_up_to_message_id,
                "updated_at": rec.updated_at,
            }

    def save_summary(
        self, session_id: str, rolling_summary: str, covers_up_to_message_id: int
    ) -> None:
        """Save or update rolling summary for a session."""
        with self.Session() as db:
            rec = db.query(SummaryRecord).filter_by(session_id=session_id).first()
            if not rec:
                rec = SummaryRecord(
                    session_id=session_id,
                    rolling_summary=rolling_summary,
                    covers_up_to_message_id=covers_up_to_message_id,
                    updated_at=datetime.utcnow(),
                )
                db.add(rec)
            else:
                rec.rolling_summary = rolling_summary
                rec.covers_up_to_message_id = covers_up_to_message_id
                rec.updated_at = datetime.utcnow()
            db.commit()

    def delete_session_data(self, session_id: str) -> bool:
        """Permanently wipe all data associated with a session ('Delete my data')."""
        with self.Session() as db:
            db.query(MessageRecord).filter_by(session_id=session_id).delete()
            db.query(CaseFileRecord).filter_by(session_id=session_id).delete()
            db.query(SummaryRecord).filter_by(session_id=session_id).delete()
            db.query(SessionRecord).filter_by(id=session_id).delete()
            db.commit()
            return True

    def prune_expired_sessions(self, expiry_days: int = 30) -> int:
        """Remove sessions inactive for longer than expiry_days."""
        cutoff = datetime.utcnow() - timedelta(days=expiry_days)
        with self.Session() as db:
            expired_sessions = (
                db.query(SessionRecord.id)
                .filter(SessionRecord.last_active_at < cutoff)
                .all()
            )
            count = 0
            for (sid,) in expired_sessions:
                self.delete_session_data(sid)
                count += 1
            return count


# Global singleton db manager
db_manager = DatabaseManager()
