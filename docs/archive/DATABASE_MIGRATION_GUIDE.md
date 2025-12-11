# SQLite to PostgreSQL Migration Guide

## Overview

This guide helps you migrate your ETPS data from local SQLite (`etps.db`) to Railway's managed PostgreSQL for production deployment.

---

## Why PostgreSQL?

- **Production-ready**: Better concurrency, reliability, and performance
- **Managed by Railway**: Automatic backups, scaling, and monitoring
- **Free tier**: Railway's Hobby plan includes PostgreSQL
- **No code changes needed**: SQLAlchemy handles both databases

---

## Migration Options

### Option 1: Fresh Start (Recommended for First Deployment)

**Best if:**
- You're deploying for the first time
- Your local data is just test data
- You want a clean production environment

**Steps:**
1. Deploy to Railway (schema auto-created)
2. Manually re-add your user profile via the API
3. Re-upload any important resume bullets

**Pros:** Clean, simple, no migration complexity  
**Cons:** Need to re-enter data

---

### Option 2: Full Data Migration

**Best if:**
- You have important data in local SQLite
- You want to preserve all bullets, jobs, and outputs

**Steps:** See detailed instructions below

---

## Option 1: Fresh Start (Step-by-Step)

### Step 1: Deploy Backend to Railway

Follow the deployment guide to deploy your backend. Railway will automatically create an empty PostgreSQL database.

### Step 2: Initialize Database Schema

The schema will be created automatically on first run, or you can manually trigger it:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link to your project
railway login
railway link

# Run schema creation
railway run python -c "from db.database import Base, engine; Base.metadata.create_all(bind=engine); print('Schema created!')"
```

### Step 3: Create Your User Profile

Use the API to create your user profile:

```bash
# Replace with your Railway backend URL
export API_URL="https://etps-production.up.railway.app"

# Create user
curl -X POST "$API_URL/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Benjamin Black",
    "email": "your.email@example.com",
    "linkedin_meta": {
      "top_skills": ["Strategy", "Analytics", "Leadership"],
      "certifications": []
    }
  }'
```

### Step 4: Add Resume Bullets

You can either:
- **Manual**: Add bullets via the API
- **Bulk**: Use the CSV import script (see below)

---

## Option 2: Full Data Migration

### Prerequisites

```bash
# Install PostgreSQL client tools (if not already installed)
# macOS:
brew install postgresql

# Verify installation
psql --version
```

### Step 1: Export SQLite Data

```bash
cd /Users/benjaminblack/projects/etps/backend

# Export to SQL dump
sqlite3 etps.db .dump > sqlite_dump.sql

# Or export specific tables
sqlite3 etps.db <<EOF
.mode insert
.output users.sql
SELECT * FROM users;
.output bullets.sql
SELECT * FROM bullets;
.output experiences.sql
SELECT * FROM experiences;
.quit
EOF
```

### Step 2: Get Railway PostgreSQL Connection String

1. Go to Railway dashboard
2. Click on your PostgreSQL database
3. Go to **Connect** tab
4. Copy the **Database URL** (looks like: `postgresql://postgres:password@host:port/railway`)

```bash
# Set as environment variable
export DATABASE_URL="postgresql://postgres:..."
```

### Step 3: Convert SQLite Dump to PostgreSQL Format

SQLite and PostgreSQL have slight syntax differences. Use this Python script:

```python
# save as migrate_sqlite_to_postgres.py
import re
import sys

def convert_sqlite_to_postgres(input_file, output_file):
    """Convert SQLite dump to PostgreSQL-compatible SQL."""
    
    with open(input_file, 'r') as f:
        sql = f.read()
    
    # Remove SQLite-specific commands
    sql = re.sub(r'BEGIN TRANSACTION;', 'BEGIN;', sql)
    sql = re.sub(r'PRAGMA.*?;', '', sql)
    sql = re.sub(r'CREATE TABLE IF NOT EXISTS', 'CREATE TABLE IF NOT EXISTS', sql)
    
    # Convert AUTOINCREMENT to SERIAL
    sql = re.sub(r'INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY', sql)
    
    # Convert DATETIME to TIMESTAMP
    sql = re.sub(r'DATETIME', 'TIMESTAMP', sql)
    
    # Remove SQLite quotes around table names (if any)
    sql = re.sub(r'"(\w+)"', r'\1', sql)
    
    with open(output_file, 'w') as f:
        f.write(sql)
    
    print(f"Converted {input_file} -> {output_file}")

if __name__ == "__main__":
    convert_sqlite_to_postgres('sqlite_dump.sql', 'postgres_dump.sql')
```

Run the converter:

```bash
python migrate_sqlite_to_postgres.py
```

### Step 4: Import to Railway PostgreSQL

```bash
# Import the converted dump
psql "$DATABASE_URL" < postgres_dump.sql

# Or use Railway CLI
railway run psql < postgres_dump.sql
```

### Step 5: Verify Migration

```bash
# Connect to PostgreSQL
psql "$DATABASE_URL"

# Check tables
\dt

# Check row counts
SELECT 'users' as table_name, COUNT(*) FROM users
UNION ALL
SELECT 'bullets', COUNT(*) FROM bullets
UNION ALL
SELECT 'experiences', COUNT(*) FROM experiences
UNION ALL
SELECT 'job_profiles', COUNT(*) FROM job_profiles;

# Exit
\q
```

---

## Option 3: Programmatic Migration (Python Script)

For more control, use this Python migration script:

```python
# save as migrate_db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, User, Bullet, Experience, JobProfile, CompanyProfile
from db.database import get_db

# Source: SQLite
SQLITE_URL = "sqlite:///etps.db"
sqlite_engine = create_engine(SQLITE_URL)
SqliteSession = sessionmaker(bind=sqlite_engine)

# Target: PostgreSQL (from Railway)
POSTGRES_URL = os.getenv("DATABASE_URL")
postgres_engine = create_engine(POSTGRES_URL)
PostgresSession = sessionmaker(bind=postgres_engine)

def migrate_data():
    """Migrate all data from SQLite to PostgreSQL."""
    
    # Create schema in PostgreSQL
    Base.metadata.create_all(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    postgres_session = PostgresSession()
    
    try:
        # Migrate Users
        users = sqlite_session.query(User).all()
        for user in users:
            postgres_session.merge(user)
        postgres_session.commit()
        print(f"Migrated {len(users)} users")
        
        # Migrate Experiences
        experiences = sqlite_session.query(Experience).all()
        for exp in experiences:
            postgres_session.merge(exp)
        postgres_session.commit()
        print(f"Migrated {len(experiences)} experiences")
        
        # Migrate Bullets
        bullets = sqlite_session.query(Bullet).all()
        for bullet in bullets:
            postgres_session.merge(bullet)
        postgres_session.commit()
        print(f"Migrated {len(bullets)} bullets")
        
        # Migrate Job Profiles
        jobs = sqlite_session.query(JobProfile).all()
        for job in jobs:
            postgres_session.merge(job)
        postgres_session.commit()
        print(f"Migrated {len(jobs)} job profiles")
        
        # Migrate Company Profiles
        companies = sqlite_session.query(CompanyProfile).all()
        for company in companies:
            postgres_session.merge(company)
        postgres_session.commit()
        print(f"Migrated {len(companies)} company profiles")
        
        print("\n✅ Migration complete!")
        
    except Exception as e:
        postgres_session.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        sqlite_session.close()
        postgres_session.close()

if __name__ == "__main__":
    migrate_data()
```

Run the migration:

```bash
# Set PostgreSQL URL from Railway
export DATABASE_URL="postgresql://postgres:..."

# Run migration
cd backend
python migrate_db.py
```

---

## Post-Migration Steps

### 1. Verify Data Integrity

```bash
# Connect to production database
psql "$DATABASE_URL"

# Check foreign key relationships
SELECT 
    b.id, 
    b.text, 
    e.company_name 
FROM bullets b 
JOIN experiences e ON b.experience_id = e.id 
LIMIT 5;

# Check for orphaned records
SELECT COUNT(*) FROM bullets WHERE experience_id NOT IN (SELECT id FROM experiences);
```

### 2. Re-index Vector Store

After migration, you need to re-index your bullets in Qdrant:

```bash
# Using Railway CLI
railway run python -c "
from services.vector_store import QdrantVectorStore, index_all_bullets
from services.embedding_service import EmbeddingService
from db.database import get_db
import asyncio

async def reindex():
    db = next(get_db())
    vector_store = QdrantVectorStore()
    embedding_service = EmbeddingService()
    count = await index_all_bullets(db, embedding_service, vector_store)
    print(f'Indexed {count} bullets')

asyncio.run(reindex())
"
```

### 3. Test Production API

```bash
# Test user endpoint
curl https://your-railway-url.up.railway.app/api/v1/users/1

# Test resume generation
curl -X POST https://your-railway-url.up.railway.app/api/v1/resume/generate \
  -H "Content-Type: application/json" \
  -d '{"job_id": 1, "user_id": 1}'
```

---

## Troubleshooting

### Error: "relation does not exist"

**Cause:** Schema not created in PostgreSQL

**Fix:**
```bash
railway run python -c "from db.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### Error: "duplicate key value violates unique constraint"

**Cause:** Trying to insert records with existing IDs

**Fix:** Use `merge()` instead of `add()` in migration script (already done in Option 3)

### Error: "could not connect to server"

**Cause:** DATABASE_URL incorrect or database not running

**Fix:**
- Verify DATABASE_URL from Railway dashboard
- Check that PostgreSQL addon is running in Railway

### Migration is slow

**Cause:** Large dataset or network latency

**Fix:**
- Use batch inserts (modify script to commit every 100 records)
- Run migration from a server closer to Railway's region
- Consider using `pg_dump` and `pg_restore` for very large databases

---

## Rollback Plan

If migration fails, you can always:

1. **Keep using SQLite locally** for development
2. **Redeploy Railway** with fresh database
3. **Try migration again** with corrected script

Your local `etps.db` is never modified during migration, so it's always safe to retry.

---

## Best Practices

1. **Backup first**: Always keep a copy of `etps.db`
   ```bash
   cp etps.db etps_backup_$(date +%Y%m%d).db
   ```

2. **Test migration locally first**:
   - Set up local PostgreSQL
   - Test migration script
   - Verify data integrity
   - Then migrate to Railway

3. **Migrate during low traffic**: If you have users, migrate during off-hours

4. **Monitor after migration**: Check Railway logs for any database errors

---

## Recommended Approach

For your first deployment, I recommend **Option 1 (Fresh Start)**:

1. ✅ Simplest and safest
2. ✅ Clean production environment
3. ✅ No migration complexity
4. ✅ Easy to re-add your profile data

You can always migrate historical data later if needed.

---

**Questions?** Check the deployment guide or Railway documentation.
