"""Database migration commands"""
import asyncio
import sys
from alembic.config import Config
from alembic import command
from src.config.database import engine, Base
from src.config.settings import settings


def run_migrations():
    """Run database migrations"""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Migrations completed successfully!")


def create_migration(message: str = "auto migration"):
    """Create a new migration"""
    alembic_cfg = Config("alembic.ini")
    command.revision(alembic_cfg, autogenerate=True, message=message)
    print(f"Migration created with message: {message}")


def init_alembic():
    """Initialize alembic if not already initialized"""
    alembic_cfg = Config("alembic.ini")
    try:
        command.ensure_version(alembic_cfg)
        print("Alembic initialized successfully!")
    except Exception as e:
        print(f"Error initializing alembic: {e}")
        sys.exit(1)


async def create_tables():
    """Create all tables directly (for development only)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.migrate [command]")
        print("Commands:")
        print("  init      - Initialize alembic")
        print("  migrate   - Run pending migrations")
        print("  create    - Create a new migration")
        print("  tables    - Create tables directly (dev only)")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        init_alembic()
    elif cmd == "migrate":
        run_migrations()
    elif cmd == "create":
        msg = sys.argv[2] if len(sys.argv) > 2 else "auto migration"
        create_migration(msg)
    elif cmd == "tables":
        asyncio.run(create_tables())
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)