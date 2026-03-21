"""
Cron router for serverless deployment.

Provides endpoints that can be triggered by Vercel Cron or GitHub Actions
to execute scheduled background tasks.

These endpoints replace the arq worker cron jobs for serverless deployments.
"""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from glean_core import get_logger
from glean_database.models import Entry, Feed, FeedStatus, UserEntry
from glean_database.session import get_session
from glean_rss import fetch_feed, parse_feed

from .config import settings

router = APIRouter()
logger = get_logger(__name__)


async def verify_cron_secret(x_cron_secret: str | None = Header(None)) -> str:
    """
    Verify the cron secret header.

    Args:
        x_cron_secret: The X-Cron-Secret header value.

    Returns:
        The verified secret.

    Raises:
        HTTPException: If secret is missing or invalid.
    """
    # Skip verification if SERVERLESS mode is not enabled
    if not settings.serverless:
        return ""

    if not settings.cron_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRON_SECRET not configured",
        )

    if x_cron_secret != settings.cron_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron secret",
        )

    return x_cron_secret


async def fetch_single_feed_sync(session: AsyncSession, feed_id: int) -> dict[str, Any]:
    """
    Synchronously fetch a single feed (no Redis queue).

    This is a simplified version of the worker's fetch_feed_task that:
    - Fetches the feed content
    - Parses and updates entries
    - Skips full-text extraction (for speed)
    - Skips embedding enqueueing (use external queue for that)

    Args:
        session: Database session.
        feed_id: Feed ID to fetch.

    Returns:
        Dictionary with fetch results.
    """

    # Get feed
    stmt = select(Feed).where(Feed.id == feed_id)
    result = await session.execute(stmt)
    feed = result.scalar_one_or_none()

    if not feed:
        return {"status": "error", "message": "Feed not found"}

    if feed.status != FeedStatus.ACTIVE:
        return {"status": "skipped", "message": f"Feed status is {feed.status}"}

    logger.info("Fetching feed", extra={"feed_id": feed_id, "url": feed.url})

    # Fetch feed content
    fetch_result = await fetch_feed(feed.url, feed.etag, feed.last_modified)

    if fetch_result is None:
        logger.info("Feed not modified (304)", extra={"feed_id": feed_id, "url": feed.url})
        feed.last_fetched_at = datetime.now(UTC)
        await session.commit()
        return {"status": "not_modified", "feed_id": feed_id, "new_entries": 0}

    content, cache_headers = fetch_result

    # Parse feed
    parsed_feed = await parse_feed(content, feed.url)
    logger.info(
        "Parsed feed",
        extra={
            "feed_id": feed_id,
            "title": parsed_feed.title,
            "entries_count": len(parsed_feed.entries),
        },
    )

    # Update feed metadata
    feed.title = parsed_feed.title or feed.title
    feed.description = parsed_feed.description or feed.description
    feed.site_url = parsed_feed.site_url or feed.site_url
    feed.language = parsed_feed.language or feed.language
    feed.icon_url = parsed_feed.icon_url or feed.icon_url
    feed.status = FeedStatus.ACTIVE
    feed.error_count = 0
    feed.fetch_error_message = None
    feed.last_fetched_at = datetime.now(UTC)

    if cache_headers and "etag" in cache_headers:
        feed.etag = cache_headers["etag"]
    if cache_headers and "last-modified" in cache_headers:
        feed.last_modified = cache_headers["last-modified"]

    # Process entries (skip full-text extraction for speed)
    new_entries = 0
    for parsed_entry in parsed_feed.entries:
        # Check if entry already exists
        stmt = select(Entry).where(
            Entry.feed_id == feed.id, Entry.guid == parsed_entry.guid
        )
        result = await session.execute(stmt)
        existing_entry = result.scalar_one_or_none()

        if existing_entry:
            continue

        # Create new entry (without full-text extraction)
        entry = Entry(
            feed_id=feed.id,
            guid=parsed_entry.guid,
            title=parsed_entry.title,
            url=parsed_entry.url,
            content=parsed_entry.content,
            summary=parsed_entry.summary,
            author=parsed_entry.author,
            published_at=parsed_entry.published_at,
            fetched_at=datetime.now(UTC),
        )
        session.add(entry)
        new_entries += 1

    await session.commit()

    logger.info(
        "Feed fetched successfully",
        extra={"feed_id": feed_id, "new_entries": new_entries},
    )

    return {
        "status": "success",
        "feed_id": feed_id,
        "new_entries": new_entries,
        "total_entries": len(parsed_feed.entries),
    }


@router.post("/fetch-feeds")
async def cron_fetch_feeds(
    session: Annotated[AsyncSession, Depends(get_session)],
    _secret: Annotated[str, Depends(verify_cron_secret)],
    limit: int = 10,
) -> dict[str, Any]:
    """
    Fetch active feeds (serverless cron endpoint).

    This endpoint is designed for Vercel Cron or GitHub Actions.
    It fetches a limited number of feeds per invocation to avoid timeouts.

    Args:
        session: Database session.
        _secret: Verified cron secret.
        limit: Maximum number of feeds to fetch (default 10).

    Returns:
        Dictionary with fetch statistics.
    """
    logger.info("Running scheduled feed fetch", extra={"limit": limit})

    # Get feeds due for fetching (skip full-text extraction)
    now = datetime.now(UTC)
    stmt = (
        select(Feed)
        .where(
            Feed.status == FeedStatus.ACTIVE,
            (Feed.next_fetch_at.is_(None)) | (Feed.next_fetch_at <= now),
        )
        .limit(limit)
    )
    result = await session.execute(stmt)
    feeds = result.scalars().all()

    logger.info("Found feeds to fetch", extra={"count": len(feeds)})

    results = []
    for feed in feeds:
        try:
            result = await fetch_single_feed_sync(session, feed.id)
            results.append(result)

            # Update next_fetch_at for next scheduled fetch
            feed.next_fetch_at = now  # Reset for next cycle
            await session.commit()
        except Exception as e:
            logger.error("Failed to fetch feed", extra={"feed_id": feed.id, "error": str(e)})
            results.append({"feed_id": feed.id, "status": "error", "message": str(e)})

            # Update error count and schedule retry
            feed.error_count = (feed.error_count or 0) + 1
            if feed.error_count >= 10:
                feed.status = FeedStatus.ERROR
                logger.warning(
                    "Feed disabled after 10 consecutive errors",
                    extra={"feed_id": feed.id},
                )
            else:
                logger.info(
                    "Feed fetch failed, scheduling retry",
                    extra={"feed_id": feed.id, "error_count": feed.error_count},
                )
                feed.next_fetch_at = now

            await session.commit()

    return {
        "status": "completed",
        "feeds_processed": len(results),
        "results": results,
    }


@router.post("/cleanup")
async def cron_cleanup(
    session: Annotated[AsyncSession, Depends(get_session)],
    _secret: Annotated[str, Depends(verify_cron_secret)],
) -> dict[str, Any]:
    """
    Cleanup expired read-later entries (serverless cron endpoint).

    This endpoint is designed for Vercel Cron or GitHub Actions.
    It cleans up user entries where read_later is True but read_later_until has passed.

    Args:
        session: Database session.
        _secret: Verified cron secret.

    Returns:
        Dictionary with cleanup statistics.
    """
    logger.info("Running scheduled cleanup")

    now = datetime.now(UTC)

    # Find and update expired entries
    stmt = (
        update(UserEntry)
        .where(
            and_(
                UserEntry.read_later.is_(True),
                UserEntry.read_later_until.isnot(None),
                UserEntry.read_later_until < now,
            )
        )
        .values(read_later=False, read_later_until=None)
    )
    result = await session.execute(stmt)
    cleaned_count = result.rowcount or 0

    logger.info("Cleanup completed", extra={"cleaned_count": cleaned_count})

    return {
        "status": "completed",
        "cleaned_count": cleaned_count,
    }
