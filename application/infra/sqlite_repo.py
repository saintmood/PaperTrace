import json
import logging
import os
import sqlite3

from application.interfaces import IRepository
from application.models import ArticleMetadata, ArticleState

logger = logging.getLogger(__name__)


class SQLiteRepository(IRepository):
    def __init__(self, db_name: str = "papertrace.db"):
        self.file_path = os.path.join(os.getcwd(), db_name)
        self._init_db()

    def _init_db(self):
        """Single method to initialize the DB. The 'with' context manager automatically closes the connection."""
        with sqlite3.connect(self.file_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    authors TEXT NOT NULL,
                    abstract TEXT,
                    keywords TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    proposed_filename TEXT,
                    status TEXT DEFAULT 'PENDING_REVIEW' CHECK(status IN ('APPROVED', 'ARCHIVED', 'PENDING_REVIEW', 'REJECTED', 'RAW'))
                )
            """)

    def save_article(
        self,
        metadata: ArticleMetadata,
        proposed_filename: str = None,
        status: str = ArticleState.APPROVED,
    ):
        """Accepts a domain model, serializes lists, and saves to the DB."""
        # SQLite doesn't understand lists natively, so we convert them to JSON strings
        authors_json = json.dumps(metadata.authors, ensure_ascii=False)
        keywords_json = json.dumps(metadata.keywords, ensure_ascii=False)

        with sqlite3.connect(self.file_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO articles (title, authors, abstract, keywords, status, proposed_filename)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    metadata.title,
                    authors_json,
                    metadata.abstract,
                    keywords_json,
                    status,
                    proposed_filename,
                ),
            )
            logger.info(f"💾 Article '{metadata.title[:30]}...' successfully saved.")

    def get_articles(self) -> list[dict]:
        """Senior approach: return dictionaries instead of tuples for easier frontend/logic integration."""
        with sqlite3.connect(self.file_path) as conn:
            # This setting forces SQLite to return rows as dictionaries (by column keys)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articles")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_article_status(self, article_id: int, status: str):
        """Corrected update method with proper column names."""
        with sqlite3.connect(self.file_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE articles SET status = ? WHERE id = ?",
                (status, article_id),
            )

    def delete_article(self, article_id: int):
        with sqlite3.connect(self.file_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
