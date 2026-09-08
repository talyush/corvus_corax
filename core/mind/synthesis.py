"""Corvus Mind — Yanıt Sentezi (Response Synthesizer).

Şablon seçici DEĞİL. Her yanıt; gerçek hafıza (topics, geçmiş turlar,
iç-gözlemler), kullanıcı modeli (profil, ilgi), iç durum (mood, drive) ve
grafik bağlamından (ContextManager) beslenerek KOMPOZE edilir.

Bir soru aynı olsa bile yanıt asla birebir aynı olmaz — çünkü hafıza,
iç-gözlem ve kullanıcı modeli her tur değişir. Bu "dynamic response".
"""

from __future__ import annotations
from typing import Dict, List


class ResponseSynthesizer:
    """MindBrain bileşenlerinden yararlanarak yanıt kurar."""

    def __init__(self, mind):
        self.mind = mind   # MindBrain (memory, user, state erişimi)

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
            "emotional": self._emotional,
            "evaluative": self._evaluative,
            "investigate": self._investigate,
            "conversational": self._conversational,
        }
        handler = dispatch.get(r, self._conversational)
        core = handler(parsed, context)
        tail = self._memory_tail(parsed, context)
        if tail:
            core = core + " " + tail
        return core

    # ------------------------------------------------------------------
    # Yardımcılar
    # ------------------------------------------------------------------
    def _lang(self, parsed) -> str:
        return parsed.language

    def _memory_tail(self, parsed, context: Dict) -> str:
        """Konuşma hafızasına dayalı kapanış: Corvus'un bildiğini gösterir."""
        tr = self._lang(parsed) == "tr"
        topics_before = self.mind.memory.all_user_topics()
        if len(topics_before) >= 2:
            if tr:
                return f"Şu ana kadar {self.mind.memory.turn_no} adımda {', '.join(topics_before[:3])} gibi konulara değindik."
            return f"So far across {self.mind.memory.turn_no} turns we've touched on {', '.join(topics_before[:3])}."
        return ""

    def _observation(self) -> str:
        """Yanıtı iç-durumdan biraz yönlendirir."""
        return self.mind.state.emotional_blend()
# ------------------------------------------------------------------
    # Register handler'ları
    # ------------------------------------------------------------------
    def _social(self, p, ctx) -> str:
        tr = self._lang(p) == "tr"
        name = self.mind.user.name_hint
        greeting = f"Merhaba{', ' + name if name else ''}!" if tr else (f"Hello{' ' + name if name else ''}!")
        n_ent, n_rel = self._graph_count(ctx)
        if n_ent > 0:
            addition = f" Şu an izleniyor: {n_ent} varlık / {n_rel} ilişki." if tr else f" Tracking {n_ent} entities / {n_rel} relations."
        else:
            addition = " Nasıl yardımcı olabilirim?" if tr else " How can I help?"
        return greeting + addition

    def _meta_corvus(self, p, ctx) -> str:
        tr = self._lang(p) == "tr"
        n_ent, n_rel = self._graph_count(ctx)
        turn = self.mind.state.turn_count
        if "statik" in p.raw_text.lower() or "dinamik" in p.raw_text.lower():
            if tr:
                return (
                    f"Cevabım birebir statik değil: her seferinde hafızama ({turn} tur), "
                    f"iç-gözlemlerime ve {n_ent} varlık / {n_rel} ilişki bağlamına bakıp cümle kurarım. "
                    f"İç durumum şu an {self._observation()}."
                )
            return (
                f"My answers aren't statically identical: each turn I compose using memory ({turn} turns), "
                f"inner observations, and the graph '{n_ent} entities / {n_rel} relations'. "
                f"I'm currently {self._observation()}."
            )
        if tr:
            return f"Ben kendi beynimle çalışıyorum — bir bot değilim. {turn} tur hafıza birikti, {self._observation()} moddayım."
        return f"I run on my own symbolic mind, not a scripted bot. {turn} turns remembered; I'm in {self._observation()} mode."

    def _identity_user(self, p, ctx) -> str:
        tr = self._lang(p) == "tr"
        profile = self.mind.user.profile_statement()
        name = self.mind.user.name_hint
        if tr:
            base = ("Profiline bakayım: " + "; ".join(profile) + ".")
            if name:
                base = f"Adın {name}. " + base
            stance = "Seni anlamaya çalışıyorum — söylediklerin modelimi şekillendiriyor."
        else:
            base = "Let me look at your profile: " + "; ".join(profile) + "."
            if name:
                base = f"Your name is {name}. " + base
            stance = "I'm working to understand you — your words shape my model of you."
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
                base = "Anlam, bir veri parçası değil; onun başka şeylerle kurduğu bağdır. Yalnız bir nokta sessizdir, bağlanınca fısıldar."
            else:
                base = "Meaning isn't a data point; it's the connection a thing forms with others. A lone node is silent; once linked, it whispers."
        else:
            if tr:
                base = "Felsefi bir soru, analitik sistemlerin de ufkunu açar: ölçebiliriz ama o ölçümün değerini ancak sorgulama kurar."
            else:
                base = "A philosophical question widens an analytical system's horizon: we can measure, but inquiry alone sets its value."
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
            base = ("Bunu paylaştığın için teşekkür ederim. Zorsa, adım adım gidebiliriz; acele etmiyoruz." if neg
                    else "Bu enerji güzel — bunu işe çevirebiliriz. Nereden başlayalım?")
            note = f" (İç durumum: {self._observation()})"
        else:
            base = ("Thank you for sharing that. If it's hard, we can go step by step — we're not in a hurry." if neg
                    else "That energy is good — we can harness it. Where shall we begin?")
            note = f" (Inner state: {self._observation()})"
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
            if tr:
                return f"Devam edelim. Üzerinde durduğumuz '{', '.join(topics[:2])}' konusuna bağlı kalabilir ya da yeni bir yön izleyebiliriz — sen bilirsin."
            return f"Let's continue. We can stay with '{', '.join(topics[:2])}' or take a new direction — your call."
        if tr:
            return "Seni dinliyorum. Ne üzerine konuşmak istersin — istihbarat, bir hedef, ya da sadece düşünceler?"
        return "I'm listening. What would you like to explore — intelligence, a target, or just thoughts?"