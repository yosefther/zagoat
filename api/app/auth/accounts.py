from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.providers import OAuthError, Profile
from app.models import OAuthAccount, User


def sign_in_with_profile(db: Session, provider: str, profile: Profile) -> User:
    """Find or create the user behind an OAuth profile.

    A known provider account signs straight in. Otherwise a verified email links the new
    provider to an existing user with that email, or creates a new user.
    """
    account = db.scalar(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == profile.provider_user_id,
        )
    )
    if account is not None:
        user = account.user
        user.name = profile.name or user.name
        user.avatar_url = profile.avatar_url or user.avatar_url
        return user

    if not profile.email or not profile.email_verified:
        raise OAuthError("email_unverified")

    email = profile.email.lower()
    user_or_none = db.scalar(select(User).where(User.email == email))
    if user_or_none is None:
        user = User(email=email, name=profile.name, avatar_url=profile.avatar_url)
        db.add(user)
    else:
        user = user_or_none
    user.oauth_accounts.append(
        OAuthAccount(provider=provider, provider_user_id=profile.provider_user_id)
    )
    db.flush()
    return user
