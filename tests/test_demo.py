import json

import approval.app
from approval.demo import SOURCE, build


def campaigns():
    return sorted(p.parent.name for p in (SOURCE / "runs").glob("*/campaign.json"))


def test_demo_pages_load_from_the_committed_data():
    client = build().test_client()
    page = client.get("/").get_data(as_text=True)
    assert "Hosted demo" in page and all(run in page for run in campaigns())
    for run in campaigns():
        assert client.get(f"/run/{run}").status_code == 200
    page = client.get("/results").get_data(as_text=True)
    assert "SAMPLE" in page and "Recommendation 1" in page


def test_demo_never_calls_the_models(monkeypatch):
    started = []
    monkeypatch.setattr(approval.app, "_start_run", lambda *args: started.append(args))
    monkeypatch.setattr(approval.app, "MetaAPI", lambda **k: (_ for _ in ()).throw(AssertionError("API used")))
    client = build().test_client()
    run = campaigns()[-1]

    page = client.post("/recommend", follow_redirects=True).get_data(as_text=True)
    assert "off in the hosted demo" in page
    page = client.post("/recommendations/0/start", follow_redirects=True).get_data(as_text=True)
    assert "off in the hosted demo" in page
    page = client.post(f"/run/{run}/reject", data={"note": "Warmer, please", "rewrite": "1"},
                       follow_redirects=True).get_data(as_text=True)
    assert "off in the hosted demo" in page and "Rejected." in page
    assert started == []


def test_visitors_change_a_copy_not_the_committed_demo():
    before = (SOURCE / "demo_business.json").read_text()
    client = build().test_client()
    run = campaigns()[0]
    c = json.loads((SOURCE / "runs" / run / "campaign.json").read_text())
    image = next(cr["file"] for cr in c["creatives"] if cr["product_check"]["passed"])
    page = client.post(f"/run/{run}/approve", data={"image": image, "variant": "0"},
                       follow_redirects=True).get_data(as_text=True)
    assert "Approved" in page
    assert not (SOURCE / "runs" / run / "export").exists()
    assert (SOURCE / "demo_business.json").read_text() == before
