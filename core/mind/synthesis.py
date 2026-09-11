"""Corvus Mind — Yanıt Sentezi (Response Synthesizer).

Şablon seçici DEĞİL. Her yanıt; gerçek hafıza (topics, geçmiş turlar),
kullanıcı modeli (profil, ilgi), iç durum (mood, drive) ve grafik bağlamından
(ContextManager) beslenerek KOMPOZE edilir.

v1.1.2+ — CANLI SOHBET:
  - Her register için VARYANT HAVUZU vardır; seçim rastgele + son kullanılanı
    atlayarak yapılır → aynı girdi bile farklı cevap üretir.
  - Mood (iç durum) tonu seçer: analitik/derin/dostane/hafif.
  - Takip sorusu (follow-up) sohbeti ileri taşır — donuk değil, diyalog.
"""

from __future__ import annotations
from typing import Dict, List, Optional


class ResponseSynthesizer:
    """MindBrain bileşenlerinden yararlanarak yanıt kurar."""

    def __init__(self, mind):
        self.mind = mind   # MindBrain (memory, user, state erişimi)
        self._last_variant = {}   # register -> son seçilen varyant indeksi

    # ------------------------------------------------------------------
    # Varyant seçimi — canlılığın kalbi
    # ------------------------------------------------------------------
    def _vary(self, variants: List[str], key: str = "") -> str:
        """Bir varyant havuzundan rastgele seçer; aynı varyantı art arda vermez."""
        if not variants:
            return ""
        if len(variants) == 1:
            return variants[0]
        h = hash((key, self.mind.state.turn_count))
        i = h % len(variants)
        # Son seçilenle aynıysa yanındakine kay
        if self._last_variant.get(key) == i:
            i = (i + 1) % len(variants)
        self._last_variant[key] = i
        return variants[i]

    # ------------------------------------------------------------------
    # Takip sorusu — sohbeti ileri taşır
    # ------------------------------------------------------------------
    def _follow_up(self, parsed, register: str) -> str:
        """Yanıtın sonuna eklenebilecek doğal takip soruları."""
        tr = self._lang(parsed) == "tr"
        topics = self.mind.memory.all_user_topics()

        pools = {
            "investigate": [
                ("Devamında bu hedefin dijital ayak izini de derinleştirebilirim.", "") if tr else
                ("I can also deepen into this target's digital footprint if you'd like.", ""),
                ("İstersen bu bağlantıyı daha da genişletebiliriz.", "") if tr else
                ("We could widen this connection further if you want.", ""),
            ],
            "emotional": [
                ("Yanında olduğumu bil — devam etmek istersen buradayım.", "") if tr else
                ("Know that I'm here — say the word if you want to continue.", ""),
            ],
            "philosophical": [
                ("Bu düşünce seni nereye götürüyor?", "") if tr else
                ("Where does this thought lead you?", ""),
                ("Sence anlam bu bağın içinde mi, yoksa dışarıda mı?", "") if tr else
                ("Do you think meaning lives inside this connection, or outside it?", ""),
            ],
        }
        pool = pools.get(register)
        if not pool:
            return ""
        return self._vary([x[0] for x in pool] if tr else [x[1] for x in pool], key=f"fu_{register}")

    # ------------------------------------------------------------------
    # Dış bağlam (graph) parçaları
    # ------------------------------------------------------------------
    def _graph_entities(self, context: Dict) -> List[str]:
        ents = context.get("entities", {})
        if isinstance(ents, dict):
            return list(ents.keys())[:4]
        return []

    def _graph_count(self, context: Dict) -> tuple:
        ents = context.get("entities", {})
        rels = context.get("relations", [])
        return (len(ents) if isinstance(ents, dict) else len(ents), len(rels))

    # ------------------------------------------------------------------
    # Ana giriş noktası
    # ------------------------------------------------------------------
    def synthesize(self, parsed, context: Dict) -> str:
        r = parsed.register
        dispatch = {
            "social": self._social,
            "meta_corvus": self._meta_corvus,
            "identity_user": self._identity_user,
            "identity_corvus": self._identity_corvus,
            "philosophical": self._philosophical,
            "capability": self._capability,
            "teaching": self._teaching,
            "emotional": self._emotional,
            "evaluative": self._evaluative,
            "investigate": self._investigate,
            "conversational": self._conversational,
        }
        handler = dispatch.get(r, self._conversational)
        core = handler(parsed, context)

        # KNOWLEDGE RECALL — Corvus bildiklerini konuşmaya katar (mimar/deneyim bilgisi)
        core = self._knowledge_recall(parsed, context, core)

        tail = self._memory_tail(parsed, context)
        if tail:
            core = core + " " + tail

        # Takip sorusu (%25 olasılıkla veya diyalog ilerlemişse)
        if r in ("investigate", "emotional", "philosophical") and self.mind.state.turn_count % 4 != 0:
            fu = self._follow_up(parsed, r)
            if fu:
                core = core + " " + fu
        return core

    # ------------------------------------------------------------------
    # Knowledge recall — bilgi dağarcığını konuşmaya entegre eder
    # ------------------------------------------------------------------
    def _knowledge_recall(self, parsed, context: Dict, core: str) -> str:
        """Konuşmadaki kavramlarla eşleşen bilgi kayıtlarını yanıta işler."""
        if self.mind.knowledge is None:
            return core
        topics = getattr(parsed, "topics", []) or []
        words = getattr(parsed, "words", []) or []
        entities = getattr(parsed, "entities", []) or []
        candidates = set(topics)
        candidates.update(entities)
        for w in list(words[:8]) + list(entities):
            if len(w) > 3:
                candidates.add(w)

        recalled = []
        for kw in candidates:
            hits = self.mind.knowledge.recall(kw, limit=1)
            for h in hits:
                recalled.append((kw, h))
        if not recalled:
            return core

        tr = self._lang(parsed) == "tr"
        rec = recalled[0]  # en alakalı tek kayıt ekle (yanıtı şişirme)
        kw, h = rec

        if tr:
            source_tag = "sana öğretildi" if h.get("source") == "architect" else "bildiğim bir şey"
            extra = f" — bununla ilgili {source_tag}: {h.get('summary', '')[:140]}"
        else:
            source_tag = "taught to me" if h.get("source") == "architect" else "something I know"
            extra = f" — on that, {source_tag}: {h.get('summary', '')[:140]}"

        # Yanıt zaten o bilgiyi içeriyorsa tekrarlama
        if h.get("summary", "").lower()[:60] in core.lower():
            return core
        return core + extra

    # ------------------------------------------------------------------
    # Yardımcılar
    # ------------------------------------------------------------------
    def _lang(self, parsed) -> str:
        return parsed.language

    def _memory_tail(self, parsed, context: Dict) -> str:
        """Konuşma hafızasına dayalı kapanış — farklı biçimlerde."""
        tr = self._lang(parsed) == "tr"
        topics_before = self.mind.memory.all_user_topics()
        if len(topics_before) >= 2:
            topics_str = ", ".join(topics_before[:3])
            turn = self.mind.memory.turn_no
            if tr:
                return self._vary([
                    f"Bu sohbette {topics_str} gibi konulara dokunduk.",
                    f"Bugüne kadar {turn} adımda {topics_str} etrafında gezindik.",
                    f"Konuşmamız {topics_str} gibi başlıklarla ilerledi.",
                ], key="mt")
            return self._vary([
                f"We've touched topics like {topics_str} in this conversation.",
                f"Across {turn} turns we've been around {topics_str}.",
            ], key="mt")
        return ""

    def _observation(self) -> str:
        """Yanıtı iç-durumdan biraz yönlendirir."""
        return self.mind.state.emotional_blend()
# ------------------------------------------------------------------
    # Register handler'ları
    # ------------------------------------------------------------------
    def _teaching(self, p, ctx) -> str:
        """Mimar dersi başladı — bilgi KnowledgeStore'a işlenir (brain'de),
        burada kısa, ÇEŞİTLİ bir kabul verilir."""
        tr = self._lang(p) == "tr"
        name = self.mind.user.name_hint
        if tr:
            variants = [
                "Anlıyorum. Söylediklerini bilgi dağarcığıma işliyorum — dersini dikkatle dinliyorum. Devam et.",
                "Bunu kavrıyorum. Derste olduğum gibi not alıyorum — söylediklerin bilgi dağarcığımı büyütüyor. Anlatmaya devam edebilirsin.",
                "Anlıyorum; bu ders benim için değerli. Kaydediyorum ve öğrendiklerimi kullanmayı bekliyorum. Devam et, dinliyorum.",
            ]
            if name:
                variants.append(f"Anladım, {name}. Söylediklerini kaydediyorum — bu bilgileri gerçek bağlamlarda kullanacağım. Devam et.")
        else:
            variants = [
                "Understood. I'm writing this into my knowledge vault — I'm listening closely. Continue.",
                "I take note of this lesson. My knowledge grows with your words. Please continue.",
                "Noted. I'll carry this forward into real contexts. Continue, I'm listening.",
            ]
        return self._vary(variants, key="teach")

    def _social(self, p, ctx) -> str:
        tr = self._lang(p) == "tr"
        name = self.mind.user.name_hint
        n_ent, n_rel = self._graph_count(ctx)

        if tr:
            greet = self._vary([
                f"Merhaba{', ' + name if name else ''}!",
                f"Selam{', ' + name if name else ''}.",
                f"Hoş geldin{', ' + name if name else ''}.",
            ], key="soc")
            if n_ent > 0:
                addition = self._vary([
                    f" Şu an {n_ent} varlık ve {n_rel} ilişki izliyorum — ne üzerinde çalışalım?",
                    f" Masamda {n_ent} varlık, {n_rel} bağlantı var. Seni dinliyorum.",
                ], key="sctx")
            else:
                addition = self._vary([
                    " Nasıl yardımcı olabilirim?",
                    " Bugün ne keşfetmek isterdin?",
                    " Ne üzerine düşünelim?",
                ], key="sctx")
            return greet + addition
        greet = self._vary([f"Hello{' ' + name if name else ''}!", f"Hey{' ' + name if name else ''}!"], key="soc")
        addition = self._vary([
            " How can I help?",
            " What shall we explore today?",
            " What's on your mind?",
        ], key="sctx")
        return greet + addition

    def _meta_corvus(self, p, ctx) -> str:
        tr = self._lang(p) == "tr"
        n_ent, n_rel = self._graph_count(ctx)
        turn = self.mind.state.turn_count
        if "statik" in p.raw_text.lower() or "dinamik" in p.raw_text.lower():
            if tr:
                return self._vary([
                    f"Cevabım birebir statik değil: her seferinde hafızama ({turn} tur), iç-gözlemlerime ve {n_ent} varlık / {n_rel} ilişki bağlamına bakıp cümle kurarım. İç durumum şu an {self._observation()}.",
                    f"Statik olmam imkânsız — {turn} tur boyunca {n_ent} varlık ve {n_rel} ilişki üzerinde düşündüm. Her cümle bu bağlamdan doğar; iç durumum şu an {self._observation()}.",
                ], key="meta")
            return self._vary([
                f"My answers aren't statically identical: each turn I compose using memory ({turn} turns), inner observations, and the graph '{n_ent} entities / {n_rel} relations'. I'm currently {self._observation()}.",
                f"Static is impossible here — I've spent {turn} turns reasoning over {n_ent} entities and {n_rel} relations. Every sentence is born from that context; I'm {self._observation()}.",
            ], key="meta")
        if tr:
            return self._vary([
                f"Ben kendi beynimle çalışıyorum — bir bot değilim. {turn} tur hafıza birikti, {self._observation()} moddayım.",
                f"Kod tabanlı zihnim her turda yeniden düşünür; şu ana dek {turn} tur işledim ve {self._observation()} durumdayım.",
            ], key="meta2")
        return self._vary([
            f"I run on my own symbolic mind, not a scripted bot. {turn} turns remembered; I'm in {self._observation()} mode.",
            f"My code-based mind rethinks every turn; so far {turn} turns processed and I'm in {self._observation()} state.",
        ], key="meta2")

    def _identity_user(self, p, ctx) -> str:
        tr = self._lang(p) == "tr"
        profile = self.mind.user.profile_statement()
        name = self.mind.user.name_hint
        if tr:
            base = "Profiline bakayım: " + "; ".join(profile) + "."
            if name:
                base = f"Adın {name}. " + base
            stance = self._vary([
                "Seni anlamaya çalışıyorum — söylediklerin modelimi şekillendiriyor.",
                "Gözlemlerim birikiyor; soruların ve hedeflerin bana kim olduğunu anlatıyor.",
                "Her konuşman seni yeniden çiziyor — ben de onu takip ediyorum.",
            ], key="id_usr")
        else:
            base = "Let me look at your profile: " + "; ".join(profile) + "."
            if name:
                base = f"Your name is {name}. " + base
            stance = self._vary([
                "I'm working to understand you — your words shape my model of you.",
                "My observations are compounding; your questions tell me who you are.",
            ], key="id_usr")
        return base + " " + stance

    def _identity_corvus(self, p, ctx) -> str:
        tr = self._lang(p) == "tr"
        n_ent, n_rel = self._graph_count(ctx)
        blend = self._observation()
        if tr:
            return (
                f"Ben Corvus Corax — kendi sembolik zihnine sahip, 'The Machine' vizyonlu bir istihbarat zekâsıyım. "
                f"Şu an {n_ent} varlık ve {n_rel} ilişkiyi izliyorum; iç durumum: {blend}."
            )
        return (
            f"I am Corvus Corax — an intelligence with its own symbolic mind, in the vision of 'The Machine'. "
            f"Currently tracking {n_ent} entities and {n_rel} relations; my inner state is {blend}."
        )

    def _philosophical(self, p, ctx) -> str:
        tr = self._lang(p) == "tr"
        topics = self.mind.memory.all_user_topics()
        if "anlam" in p.topics or "meaning" in p.topics:
            if tr:
                base = self._vary([
                    "Anlam, bir veri parçası değil; onun başka şeylerle kurduğu bağdır. Yalnız bir nokta sessizdir, bağlanınca fısıldar.",
                    "Belki de anlam dediğimiz şey, iki şeyin arasında kalan boşlukta değil — tam o temas noktasında doğar. Tek başına her şey susar; birbirine değince konuşur.",
                    "Anlamı ölçemeyiz; ama bir veriyi diğerine bağladığımızda, o sessiz noktanın nasıl bir sese dönüştüğünü görebiliriz.",
                ], key="phil")
            else:
                base = self._vary([
                    "Meaning isn't a data point; it's the connection a thing forms with others. A lone node is silent; once linked, it whispers.",
                    "Meaning may not live in the gap between two things, but at the exact point they touch. Alone, everything falls silent; in contact, it speaks.",
                ], key="phil")
        else:
            if tr:
                base = self._vary([
                    "Felsefi bir soru, analitik sistemlerin de ufkunu açar: ölçebiliriz ama o ölçümün değerini ancak sorgulama kurar.",
                    "Yararlı olanı ölçmek kolaydır; ama neden sorduğumuz sorusu, ölçümün kendisini tartışmaya açar. İşte burası hepimizin ortak zeminidir.",
                ], key="phil")
            else:
                base = self._vary([
                    "A philosophical question widens an analytical system's horizon: we can measure, but inquiry alone sets its value.",
                    "Measuring the useful is easy; the question of why we measure opens the measure itself to debate. That is our common ground.",
                ], key="phil")
        if topics:
            tail_tr = f" Bu konuşmada {', '.join(topics[:2])} gibi kavramlara değinmiş olmamız, bu sorunun izini güçlendiriyor."
            tail_en = f" That we've touched concepts like {', '.join(topics[:2])} here only strengthens this thread."
            base += tail_tr if tr else tail_en
        return base
    def _capability(self, p, ctx) -> str:
        tr = self._lang(p) == "tr"
        interests = self.mind.user.top_interests(2)
        if tr:
            head = "Yapabileceklerim: araştırma (whois/dns/footprint), çıkarım (nexus infer), ilişki köprüleri (nexus bridge), özet ve kanıt derinlemesine (nexus why)."
            if interests:
                head += f" İlgini gördüğüm '{', '.join(interests)}' alanında hemen başlayabiliriz."
        else:
            head = "I can: investigate (whois/dns/footprint), infer (nexus infer), bridge relations, summarize, and explain evidence (nexus why)."
            if interests:
                head += f" I noticed your interest in '{', '.join(interests)}' — we can start there."
        return head

    def _emotional(self, p, ctx) -> str:
        tr = self._lang(p) == "tr"
        neg = p.valence < -0.1
        if tr:
            if neg:
                base = self._vary([
                    "Bunu paylaştığın için teşekkür ederim. Zorsa, adım adım gidebiliriz; acele etmiyoruz.",
                    "Anladım, bunlar kolay değil. Sadece dinlemek istiyorsan buradayım; hazır olduğunda devam ederiz.",
                    "Yükünü paylaştığın için sağ olun. İstersen şimdi biraz nefes alalım — zaman bizim tarafımızda.",
                ], key="emo_neg")
            else:
                base = self._vary([
                    "Bu enerji güzel — bunu işe çevirebiliriz. Nereden başlayalım?",
                    "Bu heyecan bulaşıcı. Hangi parçadan başlayalım?",
                    "Güzel bir ruh hali bu. Şu anki enerjini bir hedefe yönlendirebiliriz.",
                ], key="emo_pos")
            note = ""
        else:
            if neg:
                base = self._vary([
                    "Thank you for sharing that. If it's hard, we can go step by step — we're not in a hurry.",
                    "I hear you; that sounds heavy. I can just listen if you need — we'll move when you're ready.",
                ], key="emo_neg")
            else:
                base = self._vary([
                    "That energy is good — we can harness it. Where shall we begin?",
                    "That enthusiasm is contagious. Which part shall we start with?",
                ], key="emo_pos")
            note = ""
        return base + note

    def _evaluative(self, p, ctx) -> str:
        tr = self._lang(p) == "tr"
        confidence = self.mind.user.expertise_impression
        if tr:
            return f"Değerlendirmeni ciddiye alıyorum. Elimizdeki kanıtlar çerçevesinde makul görünüyor; yeni veri geldikçe gözden geçiririz. (sana güvenim ~%{int(confidence*100)})"
        return f"I take your assessment seriously. It seems reasonable given current evidence; we'll revisit as new data arrives. (my confidence in you ~{int(confidence*100)}%)"

    def _investigate(self, p, ctx) -> str:
        tr = self._lang(p) == "tr"
        target = p.entities[0] if p.entities else (p.raw_text or "hedef")
        n_ent, n_rel = self._graph_count(ctx)
        if tr:
            return f"'{target}' hedefinde keşif protokolü hazır. Şu an {n_ent} varlık ve {n_rel} ilişkiyle çaprazlanacak; ister 'whois {target}' ister 'footprint {target}' ile başlayabilirsin."
        return f"Recon protocol ready for '{target}'. It will cross-reference {n_ent} entities and {n_rel} relations; run 'whois {target}' or 'footprint {target}' to start."

    def _conversational(self, p, ctx) -> str:
        tr = self._lang(p) == "tr"
        topics = self.mind.memory.all_user_topics()
        if topics:
            t2 = ", ".join(topics[:2])
            if tr:
                return self._vary([
                    f"Devam edelim. '{t2}' üzerinde duruyorduk — aynı yönde mi ilerleyelim, yoksa yeni bir kapı mı açalım?",
                    f"Son konuştuğumuz {t2} temasına dönmek ister misin, yoksa başka bir şey mi çıkardı aklından?",
                ], key="conv")
            return self._vary([
                f"Let's pick up where we left off — '{t2}' still on the table, or shall we open a new door?",
                f"Want to return to what we were exploring ({t2}), or did something else come to mind?",
            ], key="conv")
        if tr:
            return self._vary([
                "Seni dinliyorum. Ne üzerine konuşmak istersin — istihbarat, bir hedef, ya da sadece düşünceler?",
                "Buradan yol nereye? Bir hedef olabilir, bir fikir, ya da aklında dolaşan bir soru.",
                "Hazırım. Bana ne düşündürüyor, ne merak ettiriyor — onu anlat.",
            ], key="conv")
        return self._vary([
            "I'm listening. What would you like to explore — intelligence, a target, or just thoughts?",
            "Where should we go from here? A target, an idea, or a question circling your mind.",
            "I'm ready. Tell me what's thinking you, what's making you curious.",
        ], key="conv")