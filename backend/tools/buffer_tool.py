"""
Buffer Tool — GraphQL API

Schedules posts to LinkedIn (Autonomous Campaign Agent page) and X/Twitter
via Buffer's GraphQL API.

Env vars required:
  BUFFER_ACCESS_TOKEN         — Personal API key from buffer.com/developers/apps
  BUFFER_LINKEDIN_CHANNEL_ID  — Buffer channel ID for the LinkedIn page
  BUFFER_TWITTER_CHANNEL_ID   — Buffer channel ID for the X/Twitter account
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import httpx
from langchain_core.tools import tool

_BUFFER_GRAPHQL = "https://api.buffer.com/graphql"

# Twitter hard limit: 280 chars
_TWITTER_CHAR_LIMIT = 280


def _headers() -> dict[str, str]:
    token = os.getenv("BUFFER_ACCESS_TOKEN")
    if not token:
        raise EnvironmentError("BUFFER_ACCESS_TOKEN not set")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _linkedin_channel_id() -> str:
    return os.getenv("BUFFER_LINKEDIN_CHANNEL_ID", "").strip()


def _twitter_channel_id() -> str:
    return os.getenv("BUFFER_TWITTER_CHANNEL_ID", "").strip()


def _truncate_for_twitter(text: str) -> str:
    """Trim text to fit Twitter's 280-char limit, ending cleanly."""
    if len(text) <= _TWITTER_CHAR_LIMIT:
        return text
    return text[: _TWITTER_CHAR_LIMIT - 3].rsplit(" ", 1)[0] + "..."


def _post_to_channel(
    channel_id: str,
    text: str,
    scheduled_at: Optional[str],
    post_now: bool = False,
) -> dict[str, Any]:
    """Post to a single Buffer channel. Returns a result dict."""
    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post { id status dueAt text }
        }
        ... on InvalidInputError  { message }
        ... on UnauthorizedError  { message }
        ... on LimitReachedError  { message }
      }
    }
    """
    if post_now:
        mode = "shareNow"
    elif scheduled_at:
        mode = "customScheduled"
    else:
        mode = "addToQueue"

    variables: dict[str, Any] = {
        "input": {
            "channelId": channel_id,
            "text": text,
            "schedulingType": "automatic",
            "mode": mode,
        }
    }
    if scheduled_at and not post_now:
        variables["input"]["dueAt"] = scheduled_at

    try:
        resp = httpx.post(
            _BUFFER_GRAPHQL,
            headers=_headers(),
            json={"query": mutation, "variables": variables},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()

        if "errors" in data:
            return {"channel_id": channel_id, "error": data["errors"][0].get("message")}

        payload = data.get("data", {}).get("createPost", {})
        if "message" in payload:
            return {"channel_id": channel_id, "error": payload["message"]}

        post = payload.get("post", {})
        return {
            "update_id": post.get("id"),
            "channel_id": channel_id,
            "status": post.get("status"),
            "scheduled_at": post.get("dueAt"),
            "text_preview": text[:120],
        }

    except httpx.HTTPStatusError as exc:
        return {
            "channel_id": channel_id,
            "error": f"Buffer API error {exc.response.status_code}: {exc.response.text[:300]}",
        }
    except Exception as exc:
        return {"channel_id": channel_id, "error": str(exc)}


@tool
def buffer_schedule_post(
    text: str,
    scheduled_at: Optional[str] = None,
    platforms: Optional[str] = "linkedin,twitter",
    post_now: bool = False,
) -> str:
    """
    Schedule or immediately publish a post via Buffer to LinkedIn and/or X/Twitter.

    Args:
        text: The post text (will be auto-trimmed for Twitter's 280-char limit).
        scheduled_at: ISO 8601 datetime string. Ignored if post_now is True.
        platforms: Comma-separated platforms: 'linkedin', 'twitter', or both.
        post_now: If True, publishes immediately instead of scheduling.

    Returns:
        JSON string with created post IDs and status for each platform.
    """
    target_platforms = [p.strip().lower() for p in (platforms or "linkedin,twitter").split(",")]
    results = []

    if "linkedin" in target_platforms:
        linkedin_id = _linkedin_channel_id()
        if linkedin_id:
            result = _post_to_channel(linkedin_id, text, scheduled_at, post_now=post_now)
            result["platform"] = "linkedin"
            results.append(result)

    if "twitter" in target_platforms:
        twitter_id = _twitter_channel_id()
        if twitter_id:
            twitter_text = _truncate_for_twitter(text)
            result = _post_to_channel(twitter_id, twitter_text, scheduled_at, post_now=post_now)
            result["platform"] = "twitter"
            results.append(result)

    return json.dumps({"success": True, "updates": results})


@tool
def buffer_get_profiles() -> str:
    """List all connected Buffer channels to verify credentials and get channel IDs."""
    try:
        query = """
        {
          account {
            currentOrganization {
              id name
              channels { id name service }
            }
          }
        }
        """
        resp = httpx.post(_BUFFER_GRAPHQL, headers=_headers(),
                          json={"query": query}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        org = data.get("data", {}).get("account", {}).get("currentOrganization", {})
        channels = [
            {"id": ch["id"], "name": ch["name"], "service": ch["service"]}
            for ch in org.get("channels", [])
        ]
        return json.dumps(channels)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def schedule_via_buffer(
    text: str,
    scheduled_at: Optional[str] = None,
    platforms: str = "linkedin,twitter",
    post_now: bool = False,
) -> dict[str, Any]:
    """Direct (non-tool) version for use inside the Publisher agent node."""
    result_str = buffer_schedule_post.invoke({
        "text": text,
        "scheduled_at": scheduled_at,
        "platforms": platforms,
        "post_now": post_now,
    })
    return json.loads(result_str)
