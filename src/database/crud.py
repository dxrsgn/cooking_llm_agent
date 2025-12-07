from contextlib import contextmanager

from sqlalchemy import select

from .models import Base, SessionLocal, User, UserProfile, engine


def init_db():
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_user_by_id(session, user_id):
    return session.get(User, user_id)


def get_user_by_login(session, login):
    stmt = select(User).where(User.login == login)
    return session.scalar(stmt)


def get_profile_by_user_id(session, user_id):
    stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    return session.scalar(stmt)

def get_profile_by_user_login(session, login):
    stmt = select(UserProfile).join(User).where(User.login == login)
    return session.scalar(stmt)

def update_profile(session, user_id, last_queries=None, preferences=None, allergies=None):
    profile = get_profile_by_user_id(session, user_id)
    if not profile:
        return None
    if last_queries is not None:
        profile.last_queries = last_queries
    if preferences is not None:
        profile.preferences = preferences
    if allergies is not None:
        profile.allergies = allergies
    session.commit()
    session.refresh(profile)
    return profile