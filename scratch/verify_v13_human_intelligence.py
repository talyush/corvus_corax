"""Verification test for Corvus Corax v1.3 Master Human Intelligence Engine."""
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.human.engine import HumanIntelligenceEngine


def test_human_intelligence():
    print("=== TEST 4: Master Human Intelligence Engine (11 Pillars) ===")
    engine = HumanIntelligenceEngine()

    target = "alexander_vance"
    sample_texts = [
        "Sistem topolojisini detaylı olarak inceledim; DNS ve TLS sertifika yapısında kritik eksiklikler mevcut.",
        "Bu nedenle altyapı güvenliğini artırmak için katı DMARC ve DNSSEC politikaları uygulamamız gerekiyor.",
        "Lütfen son raporu hemen doğrulayabilir misiniz? Log analizleri tamamlandı."
    ]
    timestamps = [
        "2026-09-22T08:30:00Z",
        "2026-09-22T10:15:00Z",
        "2026-09-22T14:45:00Z",
        "2026-09-22T16:20:00Z",
    ]
    platforms = [{"platform": "github", "status": "FOUND"}, {"platform": "twitter", "status": "FOUND"}]
    domains = [{"domain": "vance-corp.com", "has_dmarc_reject": True, "has_dnssec": True}]
    emails = ["alexander@vance-corp.com", "alex.vance@proton.me"]

    # 1. Generate Full Profile
    profile = engine.generate_human_profile(
        target=target,
        texts=sample_texts,
        timestamps=timestamps,
        platforms_data=platforms,
        domains_data=domains,
        emails=emails
    )

    print(f"[+] Human Profile generated for '{profile['target']}'")
    print(f"[+] Technical Depth: {profile['persona']['technical_depth']}")
    print(f"[+] Communication Tone: {profile['persona']['communication_tone']}")
    print(f"[+] Cognitive Style: {profile['psychology']['cognitive_style_summary']}")
    print(f"[+] Peak Hours: {profile['timing']['peak_hours_utc']}")
    print(f"[+] Email Archetype: {profile['infrastructure']['email_provider_archetype']}")

    # 2. Format Report
    report = engine.format_human_report(profile, lang="tr")
    print("\n--- Formatted Human Intelligence Report ---")
    print(report)

    assert "CORVUS HUMAN INTELLIGENCE REPORT" in report
    assert "alexander_vance" in report
    assert "DILSEL & STILOMETRIK" in report

    print("\n[+] MASTER HUMAN INTELLIGENCE ENGINE TEST PASSED CLEANLY!")
    return 0


if __name__ == "__main__":
    sys.exit(test_human_intelligence())
