"""Corvus Corax v1.2 - Corvus Decision & Huginn-Muninn Synergy Core.

"Huginn thinks, Muninn remembers, Corvus decides."

Synergy Layer:
- Muninn recalls historical snapshots, entity timeline, and attribute drift.
- Huginn evaluates current observations, evidence chains, and Bayesian hypotheses.
- Corvus synthesizes both to deliver the ultimate intelligence conclusion,
  answers "Why did the conclusion change over time?", and dictates the next operational action.
"""
from typing import Dict, Any, Optional, List
from core.muninn.recall import MuninnRecallEngine
from core.muninn.store import MuninnStore
from core.huginn.explainer import HuginnExplainer
from core.huginn.trace import ReasoningTraceModel


class CorvusDecisionCore:
    """Huginn ve Muninn'i birleştiren Corvus Üst Zihin ve Karar Motoru."""

    def __init__(self, context_manager=None, knowledge_store=None, muninn_store=None):
        self.context = context_manager
        self.knowledge = knowledge_store
        self.muninn = MuninnRecallEngine(
            store=muninn_store or MuninnStore(),
            context_manager=context_manager,
            knowledge_store=knowledge_store
        )
        self.huginn = HuginnExplainer(
            context_manager=context_manager
        )

    def evaluate_target(self, target: str) -> Dict[str, Any]:
        """Hedef için hem hafızayı (Muninn) hem muhakemeyi (Huginn) çalıştırıp Corvus kararını üretir."""
        muninn_data = self.muninn.recall_entity(target)
        huginn_trace = self.huginn.build_trace_for_target(target)

        # Karar sentezi
        has_history = muninn_data["found_in_history"]
        drift_events = muninn_data["changes"]
        confidence = huginn_trace.final_confidence

        if has_history and drift_events:
            decision_summary = (
                f"Hedef '{target}' zaman icinde {len(drift_events)} degisim gosterdi. "
                f"Guncel kanitlar ve tarihsel izler birlestirilerek %{int(confidence*100)} guvenle dogrulandi."
            )
        elif has_history:
            decision_summary = (
                f"Hedef '{target}' gecmisten bu yana stabil yapisini koruyor. "
                f"Guncel iliskilerle teyit edildi (Guven: %{int(confidence*100)})."
            )
        else:
            decision_summary = (
                f"Hedef '{target}' ilk kez gozlemlendi. "
                f"Temel istihbarat cikarimi yapildi (Guven: %{int(confidence*100)})."
            )

        next_action = huginn_trace.steps[-1].metadata.get("next_action") if huginn_trace.steps else "Monitor and correlate"

        return {
            "target": target,
            "muninn": muninn_data,
            "huginn": huginn_trace.to_dict(),
            "corvus_decision": decision_summary,
            "confidence": confidence,
            "next_action": next_action,
        }

    def explain_with_history(self, target: str, lang: str = "tr") -> str:
        """Geçmiş hafıza ve güncel muhakemeyi tek bir bütünleşik raporda sunar."""
        data = self.evaluate_target(target)
        muninn_rep = self.muninn.format_history_report(target, lang=lang)
        huginn_rep = self.huginn.explain(target, lang=lang)

        if lang == "tr":
            return (
                f"{muninn_rep}\n\n"
                f"{huginn_rep}\n\n"
                f"============================================================\n"
                f"  CORVUS NIHAI KARAR VE SONRAKI ADIM\n"
                f"============================================================\n"
                f"  * Sentezlenen Karar : {data['corvus_decision']}\n"
                f"  * Nihai Guven Skoru : %{int(data['confidence']*100)}\n"
                f"  * Onerilen Aksiyon  : {data['next_action']}\n"
                f"============================================================"
            )
        else:
            return (
                f"{muninn_rep}\n\n"
                f"{huginn_rep}\n\n"
                f"============================================================\n"
                f"  CORVUS FINAL DECISION & NEXT ACTION\n"
                f"============================================================\n"
                f"  * Synthesized Decision : {data['corvus_decision']}\n"
                f"  * Final Confidence     : {int(data['confidence']*100)}%\n"
                f"  * Recommended Action   : {data['next_action']}\n"
                f"============================================================"
            )

    def why_conclusion_changed(self, target: str, lang: str = "tr") -> str:
        """Kullanıcının 'Neden fikrin değişti?' veya 'Zaman içinde ne değişti?' sorusunu yanıtlar."""
        muninn_data = self.muninn.recall_entity(target)
        changes = muninn_data.get("changes", [])

        if not changes:
            if lang == "tr":
                return (
                    f"[Corvus // Karar Degisim Analizi]\n"
                    f"'{target}' varligi icin kayitli bir oznitelik degisimi (drift) bulunmuyor. "
                    f"Mevcut karar, ilk gozlemlenen topoloji ve kanitlarla tutarlidir."
                )
            return (
                f"[Corvus // Conclusion Drift Analysis]\n"
                f"No attribute drift recorded for entity '{target}'. "
                f"Current conclusion aligns with initial observations."
            )

        if lang == "tr":
            lines = [
                f"[Corvus // Neden Karar Degisti? (Temporal Drift Analysis)]",
                f"Hedef: '{target}' uzerinde zaman icinde su degisimler gozlemlendi:",
            ]
            for c in changes:
                t = c['timestamp'][:19].replace("T", " ")
                lines.append(f"  - [{t}] {c['attribute']} degisti: '{c['old_value']}' -> '{c['new_value']}' (Modul: {c['source_module']})")
            
            lines.append(f"\nBu degisimler Muninn tarafindan hatirlandi, Huginn bu yeni verileri kanit zincirine isledi ve Bayesian olasilik modelini guncelledi.")
            lines.append(f"Sonuc olarak Corvus, hedefin yeni risk ve iliski profilini guncelleyerek kararini revize etti.")
            return "\n".join(lines)
        else:
            lines = [
                f"[Corvus // Why Did The Conclusion Change? (Temporal Drift Analysis)]",
                f"Target: '{target}' exhibited the following historical changes:",
            ]
            for c in changes:
                t = c['timestamp'][:19].replace("T", " ")
                lines.append(f"  - [{t}] {c['attribute']} changed: '{c['old_value']}' -> '{c['new_value']}' (Source: {c['source_module']})")
            
            lines.append(f"\nMuninn recalled these shifts, Huginn integrated them into the evidence graph and updated Bayesian probabilities.")
            lines.append(f"Consequently, Corvus revised the intelligence conclusion to reflect the evolved posture.")
            return "\n".join(lines)
