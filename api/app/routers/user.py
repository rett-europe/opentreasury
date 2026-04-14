from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.models.schemas import UserPreferences, UserProfile
from app.repositories.dependencies import get_user_preferences_repo
from app.repositories.cosmos.user_preferences_repo import CosmosUserPreferencesRepository

router = APIRouter(
    prefix="/api/me",
    tags=["User"],
)


@router.get("", response_model=UserProfile)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
):
    return UserProfile(
        name=current_user["name"],
        email=current_user["email"],
        role=current_user["role"],
    )


@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: dict = Depends(get_current_user),
    repo: CosmosUserPreferencesRepository = Depends(get_user_preferences_repo),
):
    stored = await repo.get(current_user["oid"])
    if stored is None:
        return UserPreferences()
    return UserPreferences(
        language=stored.get("language", "es"),
        theme=stored.get("theme", "light"),
        compact_mode=stored.get("compactMode", False),
        reduced_motion=stored.get("reducedMotion", False),
    )


@router.put("/preferences", response_model=UserPreferences)
async def update_user_preferences(
    prefs: UserPreferences,
    current_user: dict = Depends(get_current_user),
    repo: CosmosUserPreferencesRepository = Depends(get_user_preferences_repo),
):
    prefs_dict = {
        "language": prefs.language,
        "theme": prefs.theme,
        "compactMode": prefs.compact_mode,
        "reducedMotion": prefs.reduced_motion,
    }
    await repo.upsert(current_user["oid"], prefs_dict)
    return prefs
