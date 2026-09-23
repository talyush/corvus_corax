"""Corvus Corax v1.3 - Digital Timing and Activity Rhythm Engine.

Analyzes 24-hour diurnal rhythm, peak activity windows, and probable timezones.
Ethical principle: Never assert absolute real-life routines as dogma; provide probabilistic behavioral windows.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import Counter


class ActivityRhythmEngine:
    """Dijital Zamanlama ve Aktivite Ritmi Motoru."""

    def analyze_timestamps(self, timestamps: List[str]) -> Dict[str, Any]:
        if not timestamps:
            return self._empty_rhythm()

        hours = []
        days_of_week = []

        for ts in timestamps:
            try:
                # ISO timestamp ayrıştırma
                clean_ts = ts.replace("Z", "+00:00")
                if "." in clean_ts and "+" in clean_ts:
                    # mikrosaniyeyi kırp
                    parts = clean_ts.split("+")
                    subparts = parts[0].split(".")
                    clean_ts = f"{subparts[0]}+{parts[1]}"
                dt = datetime.fromisoformat(clean_ts)
                hours.append(dt.hour)
                days_of_week.append(dt.weekday())  # 0=Monday, 6=Sunday
            except Exception:
                pass

        if not hours:
            return self._empty_rhythm()

        total_samples = len(hours)
        hour_counts = Counter(hours)
        day_counts = Counter(days_of_week)

        # 24 saatlik dağılım tablosu (00:00 - 23:00)
        hourly_distribution = {h: hour_counts.get(h, 0) for h in range(24)}

        # Peak (En Yoğun) Saatler (En çok aktivite olan 3 saat)
        top_hours = [h[0] for h in hour_counts.most_common(3)]
        
        # İnaktif / Sessiz Pencere (Muhtemel Dinlenme/Uyku Saati Adayı)
        # Ardışık en düşük aktiviteye sahip 4-6 saatlik blok
        min_window_sum = float('inf')
        quiet_start_hour = 0
        window_size = 5
        for start_h in range(24):
            window_sum = sum(hourly_distribution[(start_h + offset) % 24] for offset in range(window_size))
            if window_sum < min_window_sum:
                min_window_sum = window_sum
                quiet_start_hour = start_h

        quiet_end_hour = (quiet_start_hour + window_size) % 24

        # Muhtemel Çalışma / Uyanık Penceresi
        active_start_hour = quiet_end_hour
        active_end_hour = quiet_start_hour

        # Olasılıksal Timezone Tahmini
        # Gece yarısı 02:00-06:00 yerel saatte sessiz ise, UTC'deki sessiz pencereye göre tahmini offset hesaplanır
        estimated_tz_offset = (4 - quiet_start_hour) % 24
        if estimated_tz_offset > 12:
            estimated_tz_offset -= 24
        
        tz_str = f"UTC{'+' if estimated_tz_offset >= 0 else ''}{estimated_tz_offset}"

        day_names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        weekday_dist = {day_names[d]: day_counts.get(d, 0) for d in range(7)}

        weekday_sum = sum(day_counts.get(d, 0) for d in range(5))
        weekend_sum = sum(day_counts.get(d, 0) for d in range(5, 7))
        routine_type = "Hafta İçi Ağırlıklı (İş Rutini)" if weekday_sum > weekend_sum * 3 else "Tüm Haftaya Yaygın / Dengeli"

        return {
            "total_samples": total_samples,
            "peak_hours_utc": top_hours,
            "probable_quiet_window_utc": f"{quiet_start_hour:02d}:00 - {quiet_end_hour:02d}:00",
            "probable_active_window_utc": f"{active_start_hour:02d}:00 - {active_end_hour:02d}:00",
            "probable_timezone_estimate": f"{tz_str} (Olasılıksal Kestirim)",
            "routine_preference": routine_type,
            "hourly_distribution": hourly_distribution,
            "weekly_distribution": weekday_dist,
            "ethical_note": "Zamanlama verileri yalnızca gözlemlenen dijital izlerin olasılık dağılımıdır; kesin fiziksel rutin iddiası taşımaz.",
        }

    def _empty_rhythm(self) -> Dict[str, Any]:
        return {
            "total_samples": 0,
            "peak_hours_utc": [],
            "probable_quiet_window_utc": "Bilinmiyor",
            "probable_active_window_utc": "Bilinmiyor",
            "probable_timezone_estimate": "Bilinmiyor",
            "routine_preference": "Yetersiz Veri",
            "hourly_distribution": {h: 0 for h in range(24)},
            "weekly_distribution": {},
            "ethical_note": "Yetersiz zaman damgası kaydı.",
        }
