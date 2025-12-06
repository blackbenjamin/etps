"""
Schema Migration v1.3.0

Migrates the database from v1.2.x to v1.3.0:
- Adds new columns to users, experiences, bullets tables
- Creates engagements table
- Backs up existing data before migration
- Safe to run multiple times (idempotent)

Usage:
    cd backend
    python -m db.migrations.v1_3_0_schema_migration
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path


# Database path relative to backend directory
DB_PATH = Path(__file__).parent.parent.parent / "etps.db"
BACKUP_DIR = Path(__file__).parent / "backups"


def backup_database():
    """Create a timestamped backup of the database."""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"etps_backup_{timestamp}.db"

    if DB_PATH.exists():
        shutil.copy2(DB_PATH, backup_path)
        print(f"Backup created: {backup_path}")
        return backup_path
    else:
        print(f"No database found at {DB_PATH}, will create new")
        return None


def column_exists(cursor, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def table_exists(cursor, table: str) -> bool:
    """Check if a table exists."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    return cursor.fetchone() is not None


def migrate_users_table(cursor):
    """Add new columns to users table."""
    print("Migrating users table...")

    new_columns = [
        ("phone", "VARCHAR(50)"),
        ("portfolio_url", "VARCHAR(500)"),
        ("linkedin_url", "VARCHAR(500)"),
        ("location", "VARCHAR(255)"),
        ("candidate_profile", "JSON"),
    ]

    for col_name, col_type in new_columns:
        if not column_exists(cursor, "users", col_name):
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"  Added column: {col_name}")
        else:
            print(f"  Column exists: {col_name}")


def migrate_experiences_table(cursor):
    """Add new columns to experiences table."""
    print("Migrating experiences table...")

    new_columns = [
        ("employer_type", "VARCHAR(50)"),
        ("role_summary", "TEXT"),
        ("ai_systems_built", "JSON"),
        ("governance_frameworks_created", "JSON"),
        ("fs_domain_relevance", "FLOAT"),
        ("tools_and_technologies", "JSON"),
    ]

    for col_name, col_type in new_columns:
        if not column_exists(cursor, "experiences", col_name):
            cursor.execute(f"ALTER TABLE experiences ADD COLUMN {col_name} {col_type}")
            print(f"  Added column: {col_name}")
        else:
            print(f"  Column exists: {col_name}")


def migrate_bullets_table(cursor):
    """Add new columns to bullets table."""
    print("Migrating bullets table...")

    new_columns = [
        ("engagement_id", "INTEGER REFERENCES engagements(id)"),
        ("importance", "VARCHAR(20)"),
        ("ai_first_choice", "BOOLEAN DEFAULT 0"),
        ("order", "INTEGER DEFAULT 0"),
    ]

    for col_name, col_type in new_columns:
        if not column_exists(cursor, "bullets", col_name):
            # Handle the 'order' column which is a reserved word
            if col_name == "order":
                cursor.execute(f'ALTER TABLE bullets ADD COLUMN "order" {col_type}')
            else:
                cursor.execute(f"ALTER TABLE bullets ADD COLUMN {col_name} {col_type}")
            print(f"  Added column: {col_name}")
        else:
            print(f"  Column exists: {col_name}")


def create_engagements_table(cursor):
    """Create the engagements table."""
    print("Creating engagements table...")

    if table_exists(cursor, "engagements"):
        print("  Engagements table already exists")
        return

    cursor.execute("""
        CREATE TABLE engagements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experience_id INTEGER NOT NULL REFERENCES experiences(id),
            client VARCHAR(255),
            project_name VARCHAR(500),
            project_type VARCHAR(100),
            date_range_label VARCHAR(100),
            domain_tags JSON,
            tech_tags JSON,
            "order" INTEGER DEFAULT 0 NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at DATETIME
        )
    """)

    # Create index
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS ix_engagements_experience_id
        ON engagements(experience_id)
    """)

    print("  Created engagements table with index")


def create_indexes(cursor):
    """Create new indexes for v1.3.0 schema."""
    print("Creating indexes...")

    indexes = [
        ("ix_bullets_engagement", "bullets", "engagement_id"),
    ]

    for idx_name, table, column in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
            print(f"  Created index: {idx_name}")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                print(f"  Index exists: {idx_name}")
            else:
                raise


def run_migration():
    """Execute the full migration."""
    print("=" * 60)
    print("ETPS Schema Migration v1.3.0")
    print("=" * 60)

    # Backup first
    backup_path = backup_database()

    # Connect to database
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Run migrations
        migrate_users_table(cursor)
        migrate_experiences_table(cursor)
        create_engagements_table(cursor)
        migrate_bullets_table(cursor)
        create_indexes(cursor)

        # Commit all changes
        conn.commit()
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\nMigration failed: {e}")
        print("Database rolled back. Backup available at:", backup_path)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
