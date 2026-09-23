"""Verification test for Corvus Corax v1.3 Digital Timing & Activity Rhythm Engine."""
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.human.timing import ActivityRhythmEngine


def test_timing():
    print("=== TEST 2: Digital Timing & Activity Rhythm Engine ===")
    engine = ActivityRhythmEngine()

    # Tipik UTC 08:00 - 18:00 saatlerinde yoğunlaşan zaman damgaları
    timestamps = [
        "2026-09-20T08:15:00Z",
        "2026-09-20T09:30:00Z",
        "2026-09-20T11:45:00Z",
        "2026-09-20T14:20:00Z",
        "2026-09-20T16:10:00Z",
        "2026-09-20T17:50:00Z",
        "2026-09-21T09:00:00Z",
        "2026-09-21T10:30:00Z",
        "2026-09-21T15:00:00Z",
        "2026-09-22T08:45:00Z",
        "2026-09-22T13:15:00Z",
        "2026-09-22T16:40:00Z",
    ]

    res = engine.analyze_timestamps(timestamps)
    print(f"[+] Total Sampled Events: {res['total_samples']}")
    print(f"[+] Peak Activity Hours (UTC): {res['peak_hours_utc']}")
    print(f"[+] Probable Quiet Window (UTC): {res['probable_quiet_window_utc']}")
    print(f"[+] Probable Active Window (UTC): {res['probable_active_window_utc']}")
    print(f"[+] Probable Timezone Estimate: {res['probable_timezone_estimate']}")
    print(f"[+] Routine Preference: {res['routine_preference']}")
    print(f"[+] Ethical Note: {res['ethical_note']}")

    assert res["total_samples"] == len(timestamps)
    assert len(res["peak_hours_utc"]) > 0
    assert "UTC" in res["probable_timezone_estimate"]

    print("\n[+] DIGITAL TIMING ENGINE TEST PASSED CLEANLY!")
    return 0


if __name__ == "__main__":
    sys.exit(test_timing())
