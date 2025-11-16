"""Backfill enrichment for chats and PII detection.

- Enriched chats: first user message per chat (with first assistant reply)
  runs classification + topic + intent + quality + pii.
- PII pass: all user messages in the date window run PII detection (quality off).

Usage:
  python scripts/backfill_enrichments.py --start YYYY-MM-DD --end YYYY-MM-DD --org-id ORG

Optional flags:
  --limit N           Limit number of chats (for the enriched-chats pass)
  --batch-size N      Page size when fetching messages (default 500)
  --mode MODE         one of: both (default) | enriched_chats | pii_only
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Ensure project root is on path when running as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import supabase
from services.enrichment_service import EnrichmentService
from services.pii_service import PIIService
from dtos import EnrichmentRequestDTO
from repositories import EnrichedChatsRepository
from config import settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill enrichment for first user messages")
    parser.add_argument("--start", required=True, help="Start date (ISO, e.g. 2025-01-01)")
    parser.add_argument("--end", required=True, help="End date (ISO, e.g. 2025-01-31)")
    parser.add_argument("--org-id", required=True, help="Organization ID to attribute enrichments")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit on number of chats")
    parser.add_argument("--batch-size", type=int, default=500, help="Page size for Supabase fetches")
    parser.add_argument(
        "--mode",
        choices=["both", "enriched_chats", "pii_only"],
        default="both",
        help="Which backfill to run"
    )
    return parser.parse_args()


def fetch_first_user_messages(start: str, end: str, batch_size: int, limit: Optional[int]) -> List[Dict]:
    """Fetch first user message per chat_provider_id within date range."""

    seen_chats = set()
    first_messages: List[Dict] = []
    offset = 0

    while True:
        response = (
            supabase.table("messages")
            .select("*")
            .eq("role", "user")
            .gte("created_at", start)
            .lte("created_at", end)
            .order("chat_provider_id", desc=False)
            .order("created_at", desc=False)
            .range(offset, offset + batch_size - 1)
            .execute()
        )

        rows = response.data or []
        if not rows:
            break

        for row in rows:
            chat_id = row.get("chat_provider_id")
            if not chat_id or chat_id in seen_chats:
                continue
            seen_chats.add(chat_id)
            first_messages.append(row)
            if limit and len(first_messages) >= limit:
                return first_messages

        offset += batch_size

    return first_messages


def fetch_first_assistant_message(chat_id: str) -> Optional[Dict]:
    """Fetch the first assistant message for a chat."""
    response = (
        supabase.table("messages")
        .select("*")
        .eq("chat_provider_id", chat_id)
        .eq("role", "assistant")
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def fetch_user_messages(start: str, end: str, batch_size: int) -> List[Dict]:
    """Fetch all user messages in date window."""
    messages: List[Dict] = []
    offset = 0

    while True:
        response = (
            supabase.table("messages")
            .select("*")
            .eq("role", "user")
            .gte("created_at", start)
            .lte("created_at", end)
            .order("created_at", desc=False)
            .range(offset, offset + batch_size - 1)
            .execute()
        )

        rows = response.data or []
        if not rows:
            break

        messages.extend(rows)
        offset += batch_size

    return messages


async def enrich_messages(start: str, end: str, org_id: str, limit: Optional[int], batch_size: int):
    service = EnrichmentService()
    # Enriched chats: first user message per chat
    user_messages = fetch_first_user_messages(start, end, batch_size, limit)
    print(f"Found {len(user_messages)} chats to enrich (first user message per chat)")

    for idx, msg in enumerate(user_messages, start=1):
        chat_id = msg.get("chat_provider_id")
        content = (msg.get("content") or "").strip()
        if not content:
            print(f"[{idx}/{len(user_messages)}] Skipping chat {chat_id}: empty user content")
            continue

        assistant_msg = fetch_first_assistant_message(chat_id) if chat_id else None

        assistant_response = assistant_msg.get("content") if assistant_msg else None

        request = EnrichmentRequestDTO(
            message_id=str(msg.get("message_provider_id") or msg.get("id")),
            user_id=str(msg.get("user_id") or "unknown"),
            organization_id=org_id,
            content=content,
            role="user",
            conversation_id=chat_id,
            assistant_response=assistant_response,
            conversation_history=None,
            include_quality_analysis=True,
            include_pii_detection=True,
        )

        print(f"[{idx}/{len(user_messages)}] Enriching chat {chat_id} message {request.message_id}")
        try:
            result = await service.enrich_message(request)
            status = result.status
            print(f" -> status={status}, cache_hit={result.cache_hit}")

            # Persist to enriched_chats table
            enriched = result.result or {}
            record = {
                "chat_provider_id": chat_id,
                "first_user_message_id": request.message_id,
                "first_user_message_created_at": msg.get("created_at"),
                "first_user_message_content": content,
                "first_assistant_message_id": assistant_msg.get("message_provider_id") if assistant_msg else None,
                "first_assistant_message_content": assistant_msg.get("content") if assistant_msg else None,
                "user_id": msg.get("user_id"),
                "organization_id": org_id,
                "work_classification": enriched.get("work_classification"),
                "topic_classification": enriched.get("topic_classification"),
                "intent_classification": enriched.get("intent_classification"),
                "quality_analysis": enriched.get("quality_analysis"),
                "pii_detection": enriched.get("pii_detection"),
                "overall_confidence": enriched.get("overall_confidence"),
                "used_assistant_response": enriched.get("used_assistant_response"),
                "model_used": enriched.get("model_used", getattr(settings, "DEFAULT_MODEL", "gpt-4.1-nano")),
                "enriched_at": datetime.utcnow().isoformat(),
            }
            await EnrichedChatsRepository.save(record)
        except Exception as exc:
            print(f" -> failed: {exc}")


async def enrich_pii_only(start: str, end: str, org_id: str, batch_size: int):
    pii_service = PIIService()
    messages = fetch_user_messages(start, end, batch_size)
    print(f"Found {len(messages)} user messages for PII detection")

    for idx, msg in enumerate(messages, start=1):
        content = (msg.get("content") or "").strip()
        if not content:
            print(f"[PII {idx}/{len(messages)}] Skipping message with empty content")
            continue

        chat_id = msg.get("chat_provider_id")

        print(f"[PII {idx}/{len(messages)}] Message {msg.get('message_provider_id') or msg.get('id')}")
        try:
            pii = await pii_service.detect(content)
            record = {
                "message_id": str(msg.get("message_provider_id") or msg.get("id")),
                "user_id": str(msg.get("user_id") or "unknown"),
                "organization_id": org_id,
                "message_content": content,
                "enriched_at": datetime.utcnow().isoformat(),
                "processing_time_ms": 0,
                "work_classification": None,
                "topic_classification": None,
                "intent_classification": None,
                "quality_analysis": None,
                "pii_detection": pii,
                "overall_confidence": None,
                "used_assistant_response": False,
                "model_used": getattr(settings, "DEFAULT_MODEL", "gpt-4.1-nano"),
                "cache_hit": False,
            }
            supabase.table("message_enrichments").upsert(record).execute()
        except Exception as exc:
            print(f" -> failed: {exc}")


if __name__ == "__main__":
    args = parse_args()
    # Validate dates early
    try:
        datetime.fromisoformat(args.start)
        datetime.fromisoformat(args.end)
    except Exception:
        raise SystemExit("Start/end must be ISO format, e.g. 2025-01-01 or 2025-01-01T00:00:00")

    async def main():
        if args.mode in ("both", "enriched_chats"):
            await enrich_messages(
                start=args.start,
                end=args.end,
                org_id=args.org_id,
                limit=args.limit,
                batch_size=args.batch_size,
            )

        if args.mode in ("both", "pii_only"):
            await enrich_pii_only(
                start=args.start,
                end=args.end,
                org_id=args.org_id,
                batch_size=args.batch_size,
            )

    asyncio.run(main())
