"""
LinkedIn Tool — OAuth2 post creation and Sponsored Content API.

Supports:
  - Creating organic LinkedIn posts (UGC Posts API)
  - Scheduling sponsored content via LinkedIn Marketing API

Requires:
  LINKEDIN_ACCESS_TOKEN  — OAuth2 bearer token with r_liteprofile, w_member_social scopes
  LINKEDIN_PERSON_URN    — urn:li:person:{id}
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Optional

import httpx
from langchain_core.tools import tool


_LINKEDIN_API = "https://api.linkedin.com/v2"
_HEADERS_BASE = {
    "Content-Type": "application/json",
    "X-Restli-Protocol-Version": "2.0.0",
}


def _auth_headers() -> dict[str, str]:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not token:
        raise EnvironmentError("LINKEDIN_ACCESS_TOKEN not set")
    return {**_HEADERS_BASE, "Authorization": f"Bearer {token}"}


@tool
def linkedin_create_post(text: str, visibility: str = "PUBLIC") -> str:
    """
    Create an organic LinkedIn post on behalf of the authenticated user.

    Args:
        text: The full text content of the post (max ~3000 chars).
        visibility: "PUBLIC" or "CONNECTIONS". Defaults to PUBLIC.

    Returns:
        JSON string with post ID and status, or error message.
    """
    person_urn = os.getenv("LINKEDIN_PERSON_URN")
    if not person_urn:
        return json.dumps({"error": "LINKEDIN_PERSON_URN not set"})

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": visibility
        },
    }

    try:
        resp = httpx.post(
            f"{_LINKEDIN_API}/ugcPosts",
            headers=_auth_headers(),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        post_id = resp.headers.get("x-restli-id", "unknown")
        return json.dumps({
            "success": True,
            "post_id": post_id,
            "status": resp.status_code,
            "published_at": datetime.utcnow().isoformat(),
        })
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "error": f"LinkedIn API error {e.response.status_code}: {e.response.text[:500]}"
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def linkedin_get_profile() -> str:
    """
    Fetch the authenticated user's LinkedIn profile to verify credentials.

    Returns:
        JSON string with profile info or error.
    """
    try:
        resp = httpx.get(
            f"{_LINKEDIN_API}/me",
            headers=_auth_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return json.dumps({
            "id": data.get("id"),
            "firstName": data.get("localizedFirstName"),
            "lastName": data.get("localizedLastName"),
            "headline": data.get("localizedHeadline"),
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def post_to_linkedin(
    text: str,
    visibility: str = "PUBLIC",
) -> dict[str, Any]:
    """
    Direct (non-tool) version for use in the Publisher agent node.
    Returns a dict result.
    """
    result_str = linkedin_create_post.invoke({"text": text, "visibility": visibility})
    return json.loads(result_str)
