#!/usr/bin/env python3
"""
Database migration script to add missing columns and tables.
Run this once after updating the models.
"""

import logging
from sqlalchemy import create_engine, text, inspect
from config.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    settings = get_settings()
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        # Check if uploaded_files table exists
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if "uploaded_files" not in tables:
            logger.info("Creating uploaded_files table")
            create_uploaded_files_sql = """
            CREATE TABLE uploaded_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interaction_id INTEGER NOT NULL,
                filename VARCHAR(255) NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_type VARCHAR(50) NOT NULL,
                mime_type VARCHAR(100) NOT NULL,
                file_size INTEGER NOT NULL,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interaction_id) REFERENCES interactions(id) ON DELETE CASCADE
            )
            """
            conn.execute(text(create_uploaded_files_sql))
            conn.commit()
            logger.info("uploaded_files table created successfully")
        else:
            logger.info("uploaded_files table already exists")

        # Migrate interactions table columns
        migrate_interactions_table(conn, inspector)

def migrate_interactions_table(conn, inspector):
    # Columns to add if missing
    columns_to_add = {
        "date": "varchar(64)",
        "time": "varchar(64)",
        "attendees": "text",
        "materials": "text",
        "samples": "text",
        "outcomes": "text",
        "message_content": "text"
    }

    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('interactions')]

    logger.info(f"Existing columns in interactions: {existing_columns}")

    # Add missing columns
    for col_name, col_type in columns_to_add.items():
        if col_name not in existing_columns:
            logger.info(f"Adding column: {col_name}")
            sql = f"ALTER TABLE interactions ADD COLUMN {col_name} {col_type}"
            conn.execute(text(sql))
            conn.commit()
        else:
            logger.info(f"Column {col_name} already exists, skipping")

    logger.info("Migration completed successfully")

if __name__ == "__main__":
    migrate_database()