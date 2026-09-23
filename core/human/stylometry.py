"""Corvus Corax v1.3 - Stylometry Engine.

Advanced linguistic and stylistic feature extraction:
- Sentence & Word Length Distributions (mean, std dev, median)
- Punctuation Frequencies and Peculiarities
- Function Word Distributions (stop words / structural markers in TR & EN)
- Vocabulary Diversity (Type-Token Ratio / TTR & Hapax Legomena)
- Characteristic Phrases & N-gram Signatures
"""
import re
import math
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter


class StylometryEngine:
    """Gelişmiş Stilometrik ve Dilsel Örüntü Çıkarım Motoru."""

    # Türkçedeki yaygın işlev sözcükleri (Function / Structural Words)
    FUNCTION_WORDS_TR = {
        "ve", "veya", "ile", "için", "icin", "bu", "şu", "su", "o", "bir", "de", "da",
        "ki", "mi", "mu", "mü", "mu", "ama", "fakat", "ancak", "çünkü", "cunku", "ise",
        "gibi", "kadar", "daha", "en", "çok", "cok", "az", "bile", "artık", "artik",
        "zaten", "her", "tüm", "tum", "bütün", "butun", "bazı", "bazi", "hiç", "hic",
        "ben", "sen", "biz", "siz", "onlar", "kendi", "ne", "nasıl", "nasil", "neden",
        "nerede", "zaman", "sonra", "önce", "once", "şimdi", "simdi", "yine", "tekrar"
    }

    # İngilizcedeki yaygın işlev sözcükleri
    FUNCTION_WORDS_EN = {
        "the", "and", "a", "an", "of", "to", "in", "is", "you", "that", "it", "he", "was",
        "for", "on", "are", "as", "with", "his", "they", "i", "at", "be", "this", "have",
        "from", "or", "one", "had", "by", "word", "but", "not", "what", "all", "were",
        "we", "when", "your", "can", "said", "there", "use", "an", "each", "which", "she",
        "do", "how", "their", "if", "will", "up", "other", "about", "out", "many", "then",
        "them", "these", "so", "some", "her", "would", "make", "like", "him", "into", "time"
    }

    def analyze(self, text: str) -> Dict[str, Any]:
        """Metnin tam stilometrik parmak izini çıkarır."""
        raw_text = text.strip()
        if not raw_text:
            return self._empty_profile()

        # 1. Cümle ayrıştırma
        sentence_delimiters = re.compile(r'[.!?]+')
        sentences = [s.strip() for s in sentence_delimiters.split(raw_text) if s.strip()]
        if not sentences:
            sentences = [raw_text]

        # 2. Kelime ayrıştırma (noktalamalardan arındırılmış)
        words_raw = re.findall(r'\b[a-zA-ZçğıöşüÇĞİŞÖÜ0-9_-]+\b', raw_text)
        words_lower = [w.lower() for w in words_raw]
        total_words = len(words_lower)
        total_sentences = len(sentences)

        if total_words == 0:
            return self._empty_profile()

        # 3. İstatistiksel Hesaplamalar
        # Cümle uzunlukları (kelime bazında)
        sent_lengths = [len(re.findall(r'\b[a-zA-ZçğıöşüÇĞİŞÖÜ0-9_-]+\b', s)) for s in sentences]
        avg_sent_len = sum(sent_lengths) / max(1, total_sentences)
        var_sent_len = sum((l - avg_sent_len) ** 2 for l in sent_lengths) / max(1, total_sentences)
        std_sent_len = math.sqrt(var_sent_len)

        # Kelime uzunlukları (harf bazında)
        word_lengths = [len(w) for w in words_lower]
        avg_word_len = sum(word_lengths) / max(1, total_words)
        var_word_len = sum((l - avg_word_len) ** 2 for l in word_lengths) / max(1, total_words)
        std_word_len = math.sqrt(var_word_len)

        # 4. Sözcük Çeşitliliği (Vocabulary Diversity / Type-Token Ratio)
        unique_words = set(words_lower)
        ttr = len(unique_words) / total_words  # [0.0 - 1.0]

        word_counts = Counter(words_lower)
        # Hapax Legomena (Yalnızca 1 kez geçen kelimeler - özgün sözcük dağarcığı göstergesi)
        hapax_count = sum(1 for w, c in word_counts.items() if c == 1)
        hapax_ratio = hapax_count / max(1, len(unique_words))

        # 5. Noktalama Dağılımı ve Alışkanlıkları
        punctuation_marks = Counter(re.findall(r'[.,!?;:()"\'-/…—]', raw_text))
        total_punct = sum(punctuation_marks.values())
        punct_per_100_words = (total_punct / total_words) * 100

        # Özel noktalama özellikleri (örn: çoklu ünlem/soru işareti, elips...)
        has_multiple_exclamation = bool(re.search(r'!{2,}', raw_text))
        has_multiple_question = bool(re.search(r'\?{2,}', raw_text))
        has_ellipsis = bool(re.search(r'\.{3,}|…', raw_text))
        has_emojis_or_kaomoji = bool(re.search(r'[:;=8][-^]?[)DPOpP(\]/\\|*]|[\U00010000-\U0010ffff]', raw_text))

        # 6. İşlev Sözcükleri (Function Word Frequencies)
        # Dil tespiti: TR mi EN mi?
        tr_func_hits = sum(word_counts.get(w, 0) for w in self.FUNCTION_WORDS_TR)
        en_func_hits = sum(word_counts.get(w, 0) for w in self.FUNCTION_WORDS_EN)
        detected_lang = "tr" if tr_func_hits >= en_func_hits else "en"

        active_func_set = self.FUNCTION_WORDS_TR if detected_lang == "tr" else self.FUNCTION_WORDS_EN
        function_word_freqs = {
            w: round((word_counts[w] / total_words) * 100, 2)
            for w in active_func_set if w in word_counts
        }

        # 7. Karakteristik N-Gramlar (Tekrarlayan 2'li ve 3'lü kelime kalıpları)
        bigrams = [f"{words_lower[i]} {words_lower[i+1]}" for i in range(len(words_lower) - 1)]
        top_bigrams = Counter(bigrams).most_common(5)

        return {
            "total_words": total_words,
            "total_sentences": total_sentences,
            "detected_language": detected_lang,
            "sentence_length": {
                "mean": round(avg_sent_len, 2),
                "std_dev": round(std_sent_len, 2),
                "min": min(sent_lengths) if sent_lengths else 0,
                "max": max(sent_lengths) if sent_lengths else 0,
            },
            "word_length": {
                "mean": round(avg_word_len, 2),
                "std_dev": round(std_word_len, 2),
            },
            "vocabulary_diversity": {
                "ttr": round(ttr, 3),
                "unique_words_count": len(unique_words),
                "hapax_legomena_ratio": round(hapax_ratio, 3),
                "diversity_level": "Yüksek" if ttr > 0.75 else ("Orta" if ttr > 0.5 else "Düşük/Tekrarcı"),
            },
            "punctuation_profile": {
                "total_punctuation": total_punct,
                "frequency_per_100_words": round(punct_per_100_words, 2),
                "frequencies": dict(punctuation_marks.most_common(10)),
                "peculiarities": {
                    "multiple_exclamation": has_multiple_exclamation,
                    "multiple_question": has_multiple_question,
                    "ellipsis_usage": has_ellipsis,
                    "emoji_or_kaomoji": has_emojis_or_kaomoji,
                },
            },
            "function_word_distribution": function_word_freqs,
            "top_phrases": [b[0] for b in top_bigrams if b[1] > 1],
        }

    def compute_stylometric_similarity(self, profile_a: Dict[str, Any], profile_b: Dict[str, Any]) -> float:
        """
        İki metin stilometri profili arasındaki benzerliği [0.0 - 1.0] hesaplar.
        Metodoloji: Cümle boyu, kelime boyu, TTR ve işlev sözcüğü dağılımlarının ağırlıklı kosinüs/öklid mesafesi.
        """
        if not profile_a or not profile_b or profile_a.get("total_words", 0) == 0 or profile_b.get("total_words", 0) == 0:
            return 0.0

        scores = []

        # 1. Cümle boyu yakınlığı
        mean_s_a = profile_a.get("sentence_length", {}).get("mean", 10.0)
        mean_s_b = profile_b.get("sentence_length", {}).get("mean", 10.0)
        s_diff = abs(mean_s_a - mean_s_b) / max(1.0, mean_s_a, mean_s_b)
        scores.append(max(0.0, 1.0 - s_diff) * 0.20)

        # 2. Kelime boyu yakınlığı
        mean_w_a = profile_a.get("word_length", {}).get("mean", 5.0)
        mean_w_b = profile_b.get("word_length", {}).get("mean", 5.0)
        w_diff = abs(mean_w_a - mean_w_b) / max(1.0, mean_w_a, mean_w_b)
        scores.append(max(0.0, 1.0 - w_diff) * 0.20)

        # 3. TTR Yakınlığı
        ttr_a = profile_a.get("vocabulary_diversity", {}).get("ttr", 0.5)
        ttr_b = profile_b.get("vocabulary_diversity", {}).get("ttr", 0.5)
        ttr_diff = abs(ttr_a - ttr_b)
        scores.append(max(0.0, 1.0 - ttr_diff) * 0.25)

        # 4. İşlev sözcükleri ortaklık örtüşmesi
        fw_a = profile_a.get("function_word_distribution", {})
        fw_b = profile_b.get("function_word_distribution", {})
        common_keys = set(fw_a.keys()).union(set(fw_b.keys()))
        if common_keys:
            dot = sum(fw_a.get(k, 0.0) * fw_b.get(k, 0.0) for k in common_keys)
            norm_a = math.sqrt(sum(v ** 2 for v in fw_a.values())) or 1.0
            norm_b = math.sqrt(sum(v ** 2 for v in fw_b.values())) or 1.0
            fw_cos = dot / (norm_a * norm_b)
            scores.append(fw_cos * 0.35)
        else:
            scores.append(0.5 * 0.35)

        return round(sum(scores), 3)

    def _empty_profile(self) -> Dict[str, Any]:
        return {
            "total_words": 0,
            "total_sentences": 0,
            "detected_language": "unknown",
            "sentence_length": {"mean": 0, "std_dev": 0, "min": 0, "max": 0},
            "word_length": {"mean": 0, "std_dev": 0},
            "vocabulary_diversity": {"ttr": 0, "unique_words_count": 0, "hapax_legomena_ratio": 0, "diversity_level": "Yetersiz Veri"},
            "punctuation_profile": {"total_punctuation": 0, "frequency_per_100_words": 0, "frequencies": {}, "peculiarities": {}},
            "function_word_distribution": {},
            "top_phrases": [],
        }
