"""Corvus Perception — Wallet SourceAdapter (Wrapper).

Mevcut modules/financial_intel.py modülünü Perception pipeline'a bağlar.
Kripto cüzdan adresini, zincir tespitini ve explorer bağını normalize
eder. BTC bakiyesi canlı sorgu (blockchain.info) — anahtarsız.

Kural: on_chain (1.0) adres formatından kesin; wallet_candidate_for (0.4)
KANDİDAT — cüzdanlar paylaşılabilir, sahiplik doğrulanamaz.
"""

from __future__ import annotations

from typing import Any, Dict

from core.perception.adapter import ModuleSourceAdapter
from core.perception.model import SourceDeclaration


class WalletAdapter(ModuleSourceAdapter):
    """Financial (Wallet) Intelligence modülünü saran algı kaynağı."""

    def __init__(self, config=None, logger=None, context=None):
        from modules.financial_intel import FinancialIntelModule

        source = SourceDeclaration(
            source_id="wallet",
            kind="http",
            auth_level="public",
            base_url="https://blockchain.info",
            rate_limit=1.0,
        )
        super().__init__(
            module_cls=FinancialIntelModule,
            source=source,
            config=config,
            logger=logger,
            context=context,
        )

    # ------------------------------------------------------------------
    def normalize(self, raw: Any, target: str) -> Dict:
        out = raw if isinstance(raw, dict) else {}
        data = out.get("data", {}) or {}
        address = data.get("address") or target
        chain = data.get("chain") or "unknown"
        person = data.get("person_candidate")

        entities = []
        relations = []
        notes = []

        entities.append({
            "type": "wallet",
            "value": address,
            "properties": {"chain": chain,
                           "explorer_url": data.get("explorer_url"),
                           "balance_btc": data.get("balance_btc")},
            "provenance": {"source": "corvus", "status": "discovered"},
        })

        relations.append({
            "src": {"type": "wallet", "value": address},
            "relation": "on_chain",
            "dst": {"type": "blockchain", "value": chain},
            "confidence": 1.0,   # adres formatı zinciri kesinleştirir
        })

        # Kişi adayı (candidate — cüzdan sahiplik belirteci değil)
        if person:
            relations.append({
                "src": {"type": "person", "value": person},
                "relation": "wallet_candidate_for",
                "dst": {"type": "wallet", "value": address},
                "confidence": 0.4,
            })

        notes.append({
            "text": f"Wallet {address[:12]}... on {chain.upper()}"
                    f"{f' — balance {data.get('balance_btc')} BTC' if data.get('balance_btc') is not None else ''}",
            "severity": "info",
            "confidence": 0.9,
        })

        return {"entities": entities, "relations": relations, "notes": notes,
                "data": data}

    def _target_type(self, normalized: Dict, target: str) -> str:
        return "wallet"
