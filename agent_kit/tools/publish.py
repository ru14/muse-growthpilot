"""Post an approved export to the business's Facebook Page and Instagram account.

Only the owner starts this, from the approval screen, after approving (approval/gate.py
refuses anything else). Uses Meta's Graph API with a Page access token.

    python -m agent_kit.tools.publish --check   # shows which Page and Instagram account the token posts to

Instagram's API only takes an image by public URL, so the image is posted to Facebook
first and Instagram is given the copy Facebook hosts.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

GRAPH = "https://graph.facebook.com/v23.0"


class PublishError(RuntimeError):
    """Meta refused the post, or the setup is incomplete."""


class Graph:
    """A thin Graph API client. Errors carry Meta's message, never the token."""

    def __init__(self, token: str, http=requests) -> None:
        self.token, self.http = token, http

    def get(self, path: str, **params) -> dict:
        return self._check(self.http.get(f"{GRAPH}/{path}", params={**params, "access_token": self.token}, timeout=60))

    def post(self, path: str, data: dict, files: dict | None = None) -> dict:
        return self._check(
            self.http.post(f"{GRAPH}/{path}", data={**data, "access_token": self.token}, files=files, timeout=120)
        )

    @staticmethod
    def _check(response) -> dict:
        try:
            body = response.json()
        except ValueError:
            body = {}
        if response.status_code >= 400 or "error" in body:
            message = (body.get("error") or {}).get("message") or f"HTTP {response.status_code}"
            raise PublishError(f"Meta refused it: {message}")
        return body


def page_setup(graph: Graph, page_id: str) -> dict:
    """The Page's name and its linked Instagram account, if any."""
    page = graph.get(page_id, fields="name,instagram_business_account{id,username}")
    ig = page.get("instagram_business_account") or {}
    return {"page": page.get("name", ""), "instagram_id": ig.get("id", ""), "instagram_username": ig.get("username", "")}


def post_facebook(graph: Graph, page_id: str, image: Path, caption: str) -> dict:
    with open(image, "rb") as f:
        r = graph.post(f"{page_id}/photos", {"message": caption}, files={"source": f})
    post_id = r.get("post_id") or r["id"]
    try:  # it is posted now; a failed link lookup must not lose that
        url = graph.get(post_id, fields="permalink_url").get("permalink_url", "")
    except Exception:
        url = ""
    return {"id": post_id, "photo_id": r["id"], "url": url}


def hosted_image(graph: Graph, photo_id: str) -> str:
    """The largest copy of a Facebook photo, as a public URL."""
    images = graph.get(photo_id, fields="images").get("images") or []
    if not images:
        raise PublishError("Facebook didn't return the posted photo's address")
    return max(images, key=lambda i: i.get("width", 0))["source"]


def post_instagram(graph: Graph, ig_id: str, image_url: str, caption: str, wait: float = 2.0) -> dict:
    container = graph.post(f"{ig_id}/media", {"image_url": image_url, "caption": caption})["id"]
    for _ in range(30):  # Instagram fetches the image before it can be published
        status = graph.get(container, fields="status_code").get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise PublishError(f"Instagram couldn't use the image ({status})")
        time.sleep(wait)
    else:
        raise PublishError("Instagram took too long to prepare the post")
    media_id = graph.post(f"{ig_id}/media_publish", {"creation_id": container})["id"]
    url = graph.get(media_id, fields="permalink").get("permalink", "")
    return {"id": media_id, "url": url}


def publish_export(export: Path, done: dict, page_id: str, graph: Graph) -> dict:
    """Post the export to whichever platforms aren't done yet.

    A Facebook failure raises (nothing was posted). An Instagram failure after Facebook
    succeeded, including a network error, is returned as instagram_error, so the Facebook
    post is saved and a retry posts only to Instagram.
    """
    approval = json.loads((export / "approval.json").read_text())
    image = export / approval["image"]
    result = {k: v for k, v in done.items() if k in ("facebook", "instagram")}
    if "facebook" not in result:
        result["facebook"] = post_facebook(graph, page_id, image, (export / "facebook.txt").read_text().strip())
    if "instagram" not in result:
        try:
            ig_id = page_setup(graph, page_id)["instagram_id"]
            if not ig_id:
                raise PublishError("no Instagram account is linked to the Page (Business Suite → Settings → Accounts)")
            url = hosted_image(graph, result["facebook"]["photo_id"])
            result["instagram"] = post_instagram(graph, ig_id, url, (export / "instagram.txt").read_text().strip())
        except PublishError as e:
            result["instagram_error"] = str(e)
        except Exception as e:  # network trouble; its message can hold the request URL and token
            result["instagram_error"] = f"the request failed ({type(e).__name__}); check Instagram before trying again"
    return result


def main() -> None:
    import argparse

    from growthpilot import config

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", required=True, help="show where posts would go; posts nothing")
    parser.parse_args()
    page_id, token = config.meta_page()
    s = page_setup(Graph(token), page_id)
    print(f"Facebook Page: {s['page']}")
    print(f"Instagram: @{s['instagram_username']}" if s["instagram_id"] else "Instagram: not linked to this Page")


if __name__ == "__main__":
    main()
