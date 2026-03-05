"""Database models for newspaper archiver."""
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import json


@dataclass
class Issue:
    id: Optional[int]
    file_path: str
    guessed_date: Optional[str] = None
    issue_no: Optional[str] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class Page:
    id: Optional[int]
    issue_id: int
    page_no: int
    text: str = ""
    ocr_confidence: Optional[float] = None
    image_path: Optional[str] = None


@dataclass
class Event:
    id: Optional[int]
    issue_id: int
    page_no: int
    event_date: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    place: Optional[str] = None
    people_json: str = "[]"
    tags_json: str = "[]"
    source_quote: str = ""
    
    @property
    def people(self) -> List[str]:
        return json.loads(self.people_json)
    
    @property
    def tags(self) -> List[str]:
        return json.loads(self.tags_json)


@dataclass
class Job:
    id: Optional[int]
    input_path: str
    status: str = "queued"  # queued, processing, done, error
    progress: int = 0
    message: str = ""
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class Database:
    def __init__(self, db_path: str = "newspaper_archiver.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Issues table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    guessed_date TEXT,
                    issue_no TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Pages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_id INTEGER NOT NULL,
                    page_no INTEGER NOT NULL,
                    text TEXT,
                    ocr_confidence REAL,
                    image_path TEXT,
                    FOREIGN KEY (issue_id) REFERENCES issues(id)
                )
            """)
            
            # Events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_id INTEGER NOT NULL,
                    page_no INTEGER NOT NULL,
                    event_date TEXT,
                    title TEXT,
                    description TEXT,
                    place TEXT,
                    people_json TEXT DEFAULT '[]',
                    tags_json TEXT DEFAULT '[]',
                    source_quote TEXT NOT NULL,
                    FOREIGN KEY (issue_id) REFERENCES issues(id)
                )
            """)
            
            # Jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    input_path TEXT NOT NULL,
                    status TEXT DEFAULT 'queued',
                    progress INTEGER DEFAULT 0,
                    message TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            conn.commit()


class IssueRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, issue: Issue) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO issues (file_path, guessed_date, issue_no, created_at)
                   VALUES (?, ?, ?, ?)""",
                (issue.file_path, issue.guessed_date, issue.issue_no, issue.created_at)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_by_id(self, issue_id: int) -> Optional[Issue]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM issues WHERE id = ?", (issue_id,))
            row = cursor.fetchone()
            if row:
                return Issue(**dict(row))
            return None
    
    def get_all(self) -> List[Issue]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM issues ORDER BY created_at DESC")
            return [Issue(**dict(row)) for row in cursor.fetchall()]


class PageRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, page: Page) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO pages (issue_id, page_no, text, ocr_confidence, image_path)
                   VALUES (?, ?, ?, ?, ?)""",
                (page.issue_id, page.page_no, page.text, page.ocr_confidence, page.image_path)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_by_issue(self, issue_id: int) -> List[Page]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM pages WHERE issue_id = ? ORDER BY page_no",
                (issue_id,)
            )
            return [Page(**dict(row)) for row in cursor.fetchall()]


class EventRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, event: Event) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO events (issue_id, page_no, event_date, title, description, 
                                       place, people_json, tags_json, source_quote)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (event.issue_id, event.page_no, event.event_date, event.title,
                 event.description, event.place, event.people_json, event.tags_json,
                 event.source_quote)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_by_date(self, day: int, month: int) -> List[Event]:
        """Get events by day and month (any year)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM events 
                   WHERE event_date IS NOT NULL 
                   AND CAST(strftime('%d', event_date) AS INTEGER) = ?
                   AND CAST(strftime('%m', event_date) AS INTEGER) = ?
                   ORDER BY event_date""",
                (day, month)
            )
            return [Event(**dict(row)) for row in cursor.fetchall()]
    
    def get_by_month(self, month: int) -> List[Event]:
        """Get all events for specific month (across all years)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM events 
                   WHERE event_date IS NOT NULL 
                   AND CAST(strftime('%m', event_date) AS INTEGER) = ?
                   ORDER BY event_date""",
                (month,)
            )
            return [Event(**dict(row)) for row in cursor.fetchall()]
    
    def get_by_year_month(self, year: int, month: int) -> List[Event]:
        """Get events for specific year and month."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM events 
                   WHERE event_date IS NOT NULL 
                   AND CAST(strftime('%Y', event_date) AS INTEGER) = ?
                   AND CAST(strftime('%m', event_date) AS INTEGER) = ?
                   ORDER BY event_date""",
                (year, month)
            )
            return [Event(**dict(row)) for row in cursor.fetchall()]
    
    def get_all(self, limit: int = 100) -> List[Event]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM events ORDER BY event_date DESC LIMIT ?",
                (limit,)
            )
            return [Event(**dict(row)) for row in cursor.fetchall()]
    
    def search(self, query: str) -> List[Event]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM events 
                   WHERE title LIKE ? OR description LIKE ? OR source_quote LIKE ?
                   ORDER BY event_date DESC""",
                (f"%{query}%", f"%{query}%", f"%{query}%")
            )
            return [Event(**dict(row)) for row in cursor.fetchall()]


class JobRepository:
    def __init__(self, db: Database):
        self.db = db
    
    def create(self, job: Job) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO jobs (input_path, status, progress, message, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (job.input_path, job.status, job.progress, job.message, job.created_at)
            )
            conn.commit()
            return cursor.lastrowid
    
    def update_status(self, job_id: int, status: str, progress: int = None, message: str = None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if progress is not None:
                cursor.execute(
                    "UPDATE jobs SET status = ?, progress = ?, message = ? WHERE id = ?",
                    (status, progress, message or "", job_id)
                )
            else:
                cursor.execute(
                    "UPDATE jobs SET status = ?, message = ? WHERE id = ?",
                    (status, message or "", job_id)
                )
            conn.commit()
    
    def get_pending(self) -> List[Job]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM jobs WHERE status IN ('queued', 'processing') ORDER BY created_at"
            )
            return [Job(**dict(row)) for row in cursor.fetchall()]
    
    def get_all(self, limit: int = 100) -> List[Job]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            return [Job(**dict(row)) for row in cursor.fetchall()]
