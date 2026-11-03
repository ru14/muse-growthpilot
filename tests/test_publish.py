import json

import pytest

from agent_kit.tools import publish
from approval import gate
from approval.app import create_app
from tests.test_approval import setup  # noqa: F401  (fixture)


class Response:
    def __init__(self, body, status=200):
        self.body, self.status_code = body, status

    def json(self):
        return self.body


class FakeGraphHTTP:
    """Stands in for requests: answers the Graph API calls a post makes and records them."""

    def __init__(self, instagram_linked=True, instagram_status="FINISHED", down=()):
        self.calls, self.down = [], set(down)
        self.instagram_linked, self.instagram_status = instagram_linked, instagram_status

    def post(self, url, data, files=None, timeout=None):
        path = url.split("/v23.0/")[1]
        self.calls.append(("POST", path, {k: v for k, v in data.items() if k != "access_token"}))
        if path in self.down:
            raise ConnectionError(f"{url}?access_token=TOKEN")
        if path == "PAGE/photos":
            assert files and "source" in files
            return Response({"id": "PHOTO", "post_id": "PAGE_POST"})
        if path == "IG/media":
            return Response({"id": "CONTAINER"})
        if path == "IG/media_publish":
            return Response({"id": "MEDIA"})
        return Response({"error": {"message": f"unexpected {path}"}}, 400)

    def get(self, url, params, timeout=None):
        path = url.split("/v23.0/")[1]
        self.calls.append(("GET", path, params["fields"]))
        answers = {
            "PAGE": {"name": "Demo Weaves", **({"instagram_business_account": {"id": "IG", "username": "demoweaves"}} if self.instagram_linked else {})},
            "PAGE_POST": {"permalink_url": "https://www.facebook.com/demo/posts/1"},
            "PHOTO": {"images": [{"width": 540, "source": "https://cdn/small.jpg"}, {"width": 1080, "source": "https://cdn/big.jpg"}]},
            "CONTAINER": {"status_code": self.instagram_status},
            "MEDIA": {"permalink": "https://www.instagram.com/p/abc/"},
        }
        return Response(answers[path])


def approved(setup):
    business_file, out, run = setup
    gate.approve(run, business_file, "creative_1.png", 0, "Owner")
    return business_file, out, run


def poster(http):
    graph = publish.Graph("TOKEN", http=http)
    return lambda export, done: publish.publish_export(export, done, "PAGE", graph)


def test_posts_to_facebook_then_instagram_with_the_approved_captions(setup):
    _, _, run = approved(setup)
    http = FakeGraphHTTP()
    done = gate.publish(run, "Owner", poster(http))

    assert done["facebook"]["url"] == "https://www.facebook.com/demo/posts/1"
    assert done["instagram"]["url"] == "https://www.instagram.com/p/abc/"
    posts = {path: data for method, path, data in http.calls if method == "POST"}
    export = run / "export"
    assert posts["PAGE/photos"]["message"] == (export / "facebook.txt").read_text().strip()
    assert posts["IG/media"] == {"image_url": "https://cdn/big.jpg", "caption": (export / "instagram.txt").read_text().strip()}
    assert gate.load_campaign(run)["published"]["published_by"] == "Owner"


def test_only_an_approved_campaign_can_be_posted(setup):
    _, _, run = setup
    http = FakeGraphHTTP()
    with pytest.raises(gate.ApprovalError, match="only an approved campaign"):
        gate.publish(run, "Owner", poster(http))
    assert http.calls == []


def test_instagram_failure_keeps_facebook_and_a_retry_never_posts_twice(setup):
    _, _, run = approved(setup)
    first = FakeGraphHTTP(instagram_linked=False)
    done = gate.publish(run, "Owner", poster(first))
    assert done["facebook"] and "no Instagram account is linked" in done["instagram_error"]

    retry = FakeGraphHTTP()
    done = gate.publish(run, "Owner", poster(retry))
    assert done["instagram"]["id"] == "MEDIA"
    assert not any(path == "PAGE/photos" for _, path, _ in retry.calls)
    with pytest.raises(gate.ApprovalError, match="already posted"):
        gate.publish(run, "Owner", poster(FakeGraphHTTP()))


def test_network_error_on_instagram_keeps_the_facebook_post(setup):
    _, _, run = approved(setup)
    done = gate.publish(run, "Owner", poster(FakeGraphHTTP(down={"IG/media"})))
    assert done["facebook"]["id"] == "PAGE_POST"
    assert "ConnectionError" in done["instagram_error"] and "TOKEN" not in done["instagram_error"]

    retry = FakeGraphHTTP()
    gate.publish(run, "Owner", poster(retry))
    assert not any(path == "PAGE/photos" for _, path, _ in retry.calls)


def test_meta_errors_are_reported_without_the_token():
    graph = publish.Graph("SECRET-TOKEN", http=None)
    with pytest.raises(publish.PublishError) as e:
        graph._check(Response({"error": {"message": "Invalid OAuth access token."}}, 400))
    assert "Invalid OAuth" in str(e.value) and "SECRET" not in str(e.value)


def test_screen_needs_the_owner_to_confirm_before_posting(setup):
    business_file, out, run = approved(setup)
    http = FakeGraphHTTP()
    client = create_app(business_file, out, "Owner", make_publisher=lambda: poster(http)).test_client()
    url = f"/run/{run.name}/publish"

    page = client.post(url, follow_redirects=True).get_data(as_text=True)
    assert "tick the box" in page and http.calls == []
    page = client.post(url, data={"confirm": "1"}, follow_redirects=True).get_data(as_text=True)
    assert "Posted on Facebook and Instagram." in page and "https://www.instagram.com/p/abc/" in page


def test_a_post_made_by_hand_can_be_recorded(setup):
    business_file, out, run = approved(setup)
    client = create_app(business_file, out, "Owner").test_client()
    page = client.post(f"/run/{run.name}/posted", data={"url": "https://www.instagram.com/p/xyz/"},
                       follow_redirects=True).get_data(as_text=True)
    assert "Post link saved." in page
    published = json.loads((run / "campaign.json").read_text())["published"]
    assert published["instagram"] == {"url": "https://www.instagram.com/p/xyz/", "by_hand": True}


def test_posts_from_another_site_are_refused(setup):
    business_file, out, run = approved(setup)
    http = FakeGraphHTTP()
    client = create_app(business_file, out, "Owner", make_publisher=lambda: poster(http)).test_client()
    url = f"/run/{run.name}/publish"
    assert client.post(url, data={"confirm": "1"}, headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.post(url, data={"confirm": "1"}, headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert http.calls == []
    same = client.post(url, data={"confirm": "1"}, headers={"Origin": "https://localhost", "Sec-Fetch-Site": "same-origin"})
    assert same.status_code == 302 and http.calls
