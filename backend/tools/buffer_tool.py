"""
Buffer Tool — Schedule posts via Buffer's API v1.

Supports scheduling text posts and retrieving scheduled posts.

Requires:
  BUFFER_ACCESS_TOKEN  — OAuth2 access token
  BUFFER_PROFILE_IDS   — comma-separated profile IDs (e.g. LinkedIn profile in Buffer)
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import httpx
from langchain_core.tools import tool


_BUFFER_API = "https://api.bufferapp.com/1"


def _headers() -> dict[str, str]:
    return {"Content-Type": "application/x-www-form-urlencoded"}


def _token() -> str:
    token = os.getenv("BUFFER_ACCESS_TOKEN")
    if not token:
        raise EnvironmentError("BUFFER_ACCESS_TOKEN not set")
    return token


def _profile_ids() -> list[str]:
    raw = os.getenv("BUFFER_PROFILE_IDS", "")
    return [p.strip() for p in raw.split(",") if p.strip()]


@tool
def buffer_schedule_post(
    text: str,
    scheduled_at: Optional[str] = None,
    profile_ids: Optional[str] = None,
) -> str:
    """
    Schedule a post via Buffer to one or more social profiles.

    Args:
        text: The post text content.
        scheduled_at: ISO 8601 datetime string for scheduling (e.g. "2024-02-15T09:00:00Z").
                      If None, adds to the end of the queue.
        profile_ids: Comma-separated Buffer profile IDs. If None, uses BUFFER_PROFILE_IDS env var.

    Returns:
        JSON string with update IDs and status.
    """
    try:
        token = _token()
        ids = profile_ids.split(",") if profile_ids else _profile_ids()

        if not ids:
            return json.dumps({"error": "No Buffer profile IDs configured"})

        results = []
        for pid in ids:
            data: dict[str, Any] = {
                "text": text,
                "profile_ids[]": pid,
                "access_token": token,
            }
            if scheduled_at:
                data["scheduled_at"] = scheduled_at
            else:
                data["now"] = "false"

            resp = httpx.post(
                f"{_BUFFER_API}/updates/create.json",
                data=data,
                timeout=20,
            )
            resp.raise_for_status()
            resp_data = resp.json()

            if resp_data.get("success"):
                for update in resp_data.get("updates", []):
                    results.append({
                        "update_id": update.get("id"),
                        "profile_id": pid,
                        "status": update.get("status"),
                        "scheduled_at": update.get("scheduled_at"),
                        "text_preview": text[:100],
                    })
            else:
                results.append({"profile_id": pid, "error": resp_data.get("message", "Unknown error")})

        return json.dumps({"success": True, "updates": results})

    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"Buffer API error {e.response.status_code}: {e.response.text[:300]}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def buffer_get_profiles() -> str:
    """
    List all connected Buffer profiles (to verify credentials and get profile IDs).

    Returns:
        JSON string with profile list.
    """
    try:
        token = _token()
        resp = httpx.get(
            f"{_BUFFER_API}/profiles.json",
            params={"access_token": token},
            timeout=15,
        )
        resp.raise_for_status()
        profiles = resp.json()
        simplified = [
            {
                "id": p.get("id"),
                "service": p.get("service"),
                "service_username": p.get("service_username"),
                "formatted_service": p.get("formatted_service"),
            }
            for p in profiles
        ]
        return json.dumps(simplified)
    except Exception as e:
        return json.dumps({"error": str(e)})


def schedule_via_buffer(
    text: str,
    scheduled_at: Optional[str] = None,
) -> dict[str, Any]:
    """Direct (non-tool) version for use in the Publisher agent node."""
    result_str = buffer_schedule_post.invoke({
        "text": text,
        "scheduled_at": scheduled_at,
    })
    return json.loads(result_str)
