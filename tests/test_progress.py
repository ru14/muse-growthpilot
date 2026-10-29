import json

from agent_kit.progress import DONE, FAILED, Progress


def test_checklist_and_summary():
    p = Progress(["analyze_product", "captions_verified"])
    assert not p.complete
    p.mark("analyze_product", DONE)
    p.mark("captions_verified", FAILED, "1/3")
    p.record(1, "look at the photo", "analyze_product", {}, "Done.")
    summary = p.summary()
    assert "[done] analyze_product" in summary
    assert "[failed] captions_verified (1/3)" in summary
    assert "Turn 1: analyze_product({})" in summary


def test_failures_counts_only_the_latest_streak():
    p = Progress(["x"])
    for obs in ["FAILED: a", "Done.", "FAILED: b", "FAILED: c"]:
        p.record(1, "", "write_captions", {}, obs)
    p.record(1, "", "ask_owner", {}, "Recorded.")
    assert p.failures("write_captions") == 2
    assert p.failures("ask_owner") == 0


def test_summary_keeps_only_recent_turns_and_save_writes_json(tmp_path):
    p = Progress(["x"], tmp_path / "progress.json")
    for turn in range(1, 10):
        p.record(turn, "", "ask_owner", {"question": str(turn)}, "Recorded.")
    assert "(3 earlier turns omitted)" in p.summary()
    assert "Turn 1:" not in p.summary()
    p.save()
    assert len(json.loads((tmp_path / "progress.json").read_text())["log"]) == 9
