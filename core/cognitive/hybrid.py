"""Corvus Corax v1.1.2+ — Hybrid Recon Pipeline.

İki bilgi kaynağını birleştirir:
  1. MODÜLLER (agent) -> gerçek OSINT verisi (social, github, academic, whois, dns...)
  2. LLM SESİ  (router) -> modelin eğitim bilgisi + sentez yeteneği

Akış:
  doğal soru -> hedef çıkar -> agent modülleri çalıştır (gerçek veri)
  -> LLM'e [modül sonuçları + soru] gönder -> harmanlanmış cevap

Felsefe: modül "kanıtı" toplar, LLM "hikayeyi" anlatır. İkisi ayrışamaz —
biri verisiz anlatır (balon), diğeri sessiz veri üretir (kuru). Birlikte
Corvus'un gerçek araştırma sesi olurlar.
"""

from __future__ import annotations
from typing import Dict, List, Optional

from core.agent.agent import Agent
from core.agent.policy import Approval
from core.cognitive.providers.router import ProviderRouter


class HybridRecon:
    """Agent (modüller) + LLM (ses) birleşik araştırma hattı."""

    def __init__(self, module_registry: Dict, router: Optional[ProviderRouter] = None,
                 config: Optional[Dict] = None, logger=None, context=None,
                 approval_mode: Approval = Approval.AUTO):
        self.modules = module_registry
        self.router = router or ProviderRouter()
        self.config = config or {}
        self.logger = logger
        self.context = context
        self.approval_mode = approval_mode

    # ------------------------------------------------------------------
    def pursue(self, query: str, target: Optional[str] = None, system_prompt: str = "") -> Dict:
        """Modül+LLM harmanlı araştırma yürütür.

        target verilirse agent yalnızca o hedefi araştırır (regex'ten gelen temiz ad).
        """
        agent = Agent(
            module_registry=self.modules,
            config=self.config,
            logger=self.logger,
            context=self.context,
            approval_mode=self.approval_mode,
            ask_callback=lambda q: True,
        )
        # Hedef net ise agent'a o hedefi ver, doğal sorguyu LLM'e sakla
        investigate_query = target if target else query
        report = agent.investigate(investigate_query)

        # Modül sonuçlarını LLM için özetle
        findings = self._summarize_report(report)
        resolved = target or report.get("target", query)

        # LLM'e soruyu + gerçek veriyi birlikte gönder
        prompt = self._build_prompt(query, findings)
        result = self.router.route(
            user_prompt=prompt,
            conversation_history=[],
            context_data={},
            system_prompt=(system_prompt or
                           "Sen Corvus Corax'sın. Sana OSINT modüllerinin topladığı "
                           "GERÇEK kanıt verildi. Bu kanıtları kendi bilginle birleştirip "
                           "dürüst, dengeli bir araştırma özeti sun. Bir şey bilmiyorsan "
                           "kanıtlarla ne bulunduysa onu anlat; bilmediğini söyle."),
        )

        return {
            "target": resolved,
            "target_type": report.get("target_type"),
            "report": report,
            "observations": report.get("observations", []),
            "module_findings": findings,
            "response": result.text,
            "provenance": result.to_dict(),
        }

    # ------------------------------------------------------------------
    # Yardımcılar
    # ------------------------------------------------------------------
    def _summarize_report(self, report: Dict) -> str:
        """Agent raporundan LLM'e verilecek kısa kanıt özeti üretir."""
        parts = []
        summary = report.get("summary", {})
        parts.append(f"(çalışan araç: {summary.get('success', 0)}, "
                     f"hata: {summary.get('errors', 0)}, atlanan: {summary.get('denied', 0)})")

        for obs in report.get("observations", []):
            if obs.get("status") != "success":
                continue
            tool = obs.get("tool", "?")
            target = obs.get("target", "")
            summary_t = obs.get("summary", "")[:180]
            notes = "; ".join(obs.get("notes", [])[:3])[:200]
            ents = obs.get("new_entities", [])
            block = f"  [{tool}::{target}] {summary_t}"
            if notes:
                block += f" | notlar: {notes}"
            if ents:
                block += f" | yeni varlıklar: {', '.join(ents[:6])}"
            parts.append(block)

        if len(parts) <= 1:
            return "(hiçbir modül somut veri döndürmedi — yalnızca kendi bilgini kullan)"
        return "\n".join(parts)

    def _build_prompt(self, query: str, findings: str) -> str:
        """LLM'e giden ham prompt: araştırma sorusu + gerçek modül kanıtı."""
        return (
            f"ARAŞTIRMA SORUSU: {query}\n\n"
            f"OSINT MODÜLLERİNDEN GELEN KANITLAR:\n{findings}\n\n"
            f"Bu kanıtları kendi bilginle birleştirerek soruyu cevapl."
        )