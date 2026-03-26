# Database Migrations Guide

This project uses **Alembic** for database migrations.

## Quick Reference

```bash
# Apply existing migrations (for new team members)
make docker-migrate

# Create new migration (after model changes)
make docker-migrate-create MSG="add new column"

# List database tables
make docker-db-tables

# Reset database
make docker-db-reset
```

---

## Workflow

### For New Team Members

When you clone the repo and start the project:

```bash
# Start everything (migrations run automatically)
make docker-up

# OR manually verify
make docker-db-tables    # Check tables
make docker-migrate      # Apply migrations if needed
```

### After Model Changes

When you modify models in `src/models/`:

```bash
# 1. Create migration file
make docker-migrate-create MSG="add user avatar field"

# 2. Migration file created in alembic/versions/
#    Example: alembic/versions/abc123_add_user_avatar_field.py

# 3. Commit the migration file
git add alembic/versions/
git commit -m "feat: add user avatar migration"
```

### When Team Pulls Your Changes

When you pull code with new migrations:

```bash
git pull
make docker-migrate    # Apply new migrations
```

---

## Common Tasks

### Check Current Migration Status

```bash
# Container shell
docker compose exec app alembic current

# Show migration history
docker compose exec app alembic history
```

### Rollback Last Migration

```bash
# Undo last migration
docker compose exec app alembic downgrade -1

# Rollback to specific revision
docker compose exec app alembic downgrade <revision_id>
```

### Reset Database

```bash
# Drop all tables and re-run migrations
make docker-db-reset

# OR manually
docker compose exec app alembic downgrade base
docker compose exec app alembic upgrade head
```

### Start Fresh

```bash
# Nuclear option: remove all data
docker compose down -v    # Stop and remove volumes
make docker-up            # Start fresh
```

---

## Migration Files

Migration files are stored in `alembic/versions/`.

### Example Structure

```python
"""add user avatar field

Revision ID: abc123
Revises: xyz789
Create Date: 2024-01-16 10:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = 'xyz789'

def upgrade():
    op.add_column('users', sa.Column('avatar_url', sa.String(), nullable=True))

def downgrade():
    op.drop_column('users', 'avatar_url')
```

### Good Practices

1. **Always test migrations** - Run `upgrade` and `downgrade`
2. **Name migrations clearly** - `"add user table"`, not `"update models"`
3. **Include rollback** - Always implement `downgrade()`
4. **Commit migration files** - Don't forget to include in git

---

## Direct Commands

If you prefer running commands directly:

```bash
# Enter container shell
docker compose exec app bash

# Then run alembic commands
alembic upgrade head        # Apply all migrations
alembic downgrade -1       # Rollback one migration
alembic current            # Show current revision
alembic history            # Show migration history
alembic revision --autogenerate -m "msg"  # Create migration
```

---

## Local Development (Without Docker)

If running outside Docker:

```bash
# Install dependencies
make install

# Create migration
alembic revision --autogenerate -m "add table"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Troubleshooting

### "Target database is not up to date"

```bash
# Mark current migration as applied
alembic stamp head
```

### "Can't locate revision"

```bash
# Check migration history
docker compose exec app alembic history

# Compare with your migration file's down_revision
```

### Tables not created after migration

```bash
# Check for errors in migration
docker compose logs app

# Verify migration was applied
docker compose exec app alembic current
```