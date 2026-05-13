from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.billing.access import assert_active_pro


async def require_pro_keyword_competitor(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await assert_active_pro(db, current_user.id)
