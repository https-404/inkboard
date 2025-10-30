import asyncio
import random
import uuid
from datetime import datetime, timezone

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session
from app.db.models import (
    User,
    Article,
    Tag,
    ArticleTag,
    Clap,
    Follow,
    Comment,
)


PASSWORD_PLAIN = "Password123!"


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode(), salt).decode()


def make_username(n: int) -> str:
    return f"user{n:02d}"


def make_email(n: int) -> str:
    return f"user{n:02d}@example.com"


def sample_title(i: int) -> str:
    return f"Sample Article {i}"


def sample_subtitle(i: int) -> str:
    return f"A short subtitle for article {i}"


def sample_content(i: int) -> list[dict]:
    return [
        {"type": "heading", "content": f"Heading {i}", "metadata": {"level": 2}},
        {"type": "paragraph", "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit."},
        {"type": "quote", "content": "Simplicity is the soul of efficiency."},
    ]


async def ensure_users(db: AsyncSession, count: int = 10) -> list[User]:
    users: list[User] = []
    for i in range(1, count + 1):
        username = make_username(i)
        email = make_email(i)
        exists = await db.execute(select(User).where(User.username == username))
        if exists.scalar_one_or_none():
            continue
        user = User(
            email=email,
            username=username,
            first_name=f"User{i}",
            last_name="Test",
            hashed_password=hash_password(PASSWORD_PLAIN),
            is_active=True,
            is_verified=True,
            role="author" if i % 3 == 0 else "user",
            bio=f"Bio for {username}",
        )
        db.add(user)
        users.append(user)
    if users:
        await db.flush()
    # fetch all to return
    res = await db.execute(select(User))
    return list(res.scalars().all())


async def ensure_tags(db: AsyncSession, names: list[str]) -> list[Tag]:
    out: list[Tag] = []
    for name in names:
        slug = name.lower().replace(" ", "-")
        exists = await db.execute(select(Tag).where(Tag.slug == slug))
        tag = exists.scalar_one_or_none()
        if not tag:
            tag = Tag(name=name.lower(), slug=slug)
            db.add(tag)
            out.append(tag)
    if out:
        await db.flush()
    res = await db.execute(select(Tag))
    return list(res.scalars().all())


async def create_articles(db: AsyncSession, users: list[User], tags: list[Tag], count: int = 15) -> list[Article]:
    articles: list[Article] = []
    for i in range(1, count + 1):
        author = random.choice(users)
        title = sample_title(i)
        slug = title.lower().replace(" ", "-")
        exists = await db.execute(select(Article).where(Article.slug == slug))
        if exists.scalar_one_or_none():
            continue
        art = Article(
            author_id=author.id,
            title=title,
            subtitle=sample_subtitle(i),
            slug=slug,
            content=sample_content(i),
            status="published" if i % 2 == 0 else "draft",
            reading_time=3,
            published_at=datetime.now(timezone.utc) if i % 2 == 0 else None,
        )
        db.add(art)
        articles.append(art)
    if articles:
        await db.flush()
        # tag associations (2-3 tags each)
        for art in articles:
            for t in random.sample(tags, k=min(3, max(1, len(tags)//3))):
                db.add(ArticleTag(article_id=art.id, tag_id=t.id))
        await db.flush()
    res = await db.execute(select(Article))
    return list(res.scalars().all())


async def create_follows(db: AsyncSession, users: list[User], edges: int = 20) -> None:
    if len(users) < 2:
        return
    pairs = set()
    for _ in range(edges):
        a, b = random.sample(users, 2)
        key = (str(a.id), str(b.id))
        if key in pairs:
            continue
        pairs.add(key)
        db.add(Follow(follower_id=a.id, following_id=b.id))
    await db.flush()


async def create_claps(db: AsyncSession, users: list[User], articles: list[Article], per_article: int = 5) -> None:
    for art in articles:
        for _ in range(per_article):
            u = random.choice(users)
            count = random.randint(1, 10)
            db.add(Clap(article_id=art.id, user_id=u.id, count=count))
    await db.flush()


async def create_comments(db: AsyncSession, users: list[User], articles: list[Article], per_article: int = 3) -> None:
    for art in articles:
        # top-level comments
        parents = []
        for _ in range(per_article):
            u = random.choice(users)
            c = Comment(article_id=art.id, user_id=u.id, content="Great read!")
            db.add(c)
            parents.append(c)
        await db.flush()
        # replies
        for p in parents:
            for _ in range(2):
                u = random.choice(users)
                db.add(Comment(article_id=art.id, user_id=u.id, parent_id=p.id, content="I agree!"))
    await db.flush()


async def main() -> None:
    async with async_session() as db:
        users = await ensure_users(db, count=10)
        tags = await ensure_tags(db, [
            "python", "fastapi", "sqlalchemy", "async", "backend",
            "devops", "docker", "testing", "security", "minio"
        ])
        articles = await create_articles(db, users, tags, count=15)
        await create_follows(db, users, edges=25)
        await create_claps(db, users, articles, per_article=5)
        await create_comments(db, users, articles, per_article=3)
        await db.commit()
        print("Seed completed.")
        print(f"Users password: {PASSWORD_PLAIN}")


if __name__ == "__main__":
    asyncio.run(main())


