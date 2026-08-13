import re
import json
import urllib.request
import urllib.error

from core.module_base import BaseModule
from core.config import load_rules


class FinancialIntelModule(BaseModule):
    """
    v0.9 — Financial (Wallet) Intelligence Module.

    Kripto cüzdan adreslerini analiz eder:
    - Format doğrulama (BTC, ETH, SOL)
    - Zincir tespiti (adres formatından)
    - Blockchain explorer URL üretimi
    - Canlı bakiye sorgusu (BTC için anahtarsız)
    - Kişiye aday bağlama (wallet candidate — cüzdanlar paylaşılabilir)
    """
    name = "wallet"

    # --- Cüzdan format regex'leri ---
    BTC_P2PKH = re.compile(r"^1[1-9A-HJ-NP-Za-km-z]{25,34}$")
    BTC_P2SH = re.compile(r"^3[1-9A-HJ-NP-Za-km-z]{25,34}$")
    BTC_BECH32 = re.compile(r"^(bc1)[1-9A-HJ-NP-Za-km-z]{39,59}$")
    ETH_ADDR = re.compile(r"^0x[0-9a-fA-F]{40}$")
    SOL_ADDR = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

    def _detect_chain(self, address):
        """Adres formatından zincir tespiti yapar."""
        if not address:
            return None
        if self.BTC_P2PKH.match(address):
            return "btc"
        if self.BTC_P2SH.match(address):
            return "btc"
        if self.BTC_BECH32.match(address):
            return "btc"
        if self.ETH_ADDR.match(address):
            return "eth"
        if self.SOL_ADDR.match(address) and len(address) >= 32:
            return "sol"
        return None

    def _explorer_url(self, chain, address):
        """Zincir için blockchain explorer URL'si üretir."""
        explorers = {
            "btc": f"https://www.blockchain.com/btc/address/{address}",
            "eth": f"https://etherscan.io/address/{address}",
            "sol": f"https://solscan.io/account/{address}",
        }
        return explorers.get(chain)

    def _fetch_btc_balance(self, address, timeout=10):
        """BTC bakiyesini blockchain.info API'den çeker (anahtarsız)."""
        try:
            url = f"https://blockchain.info/balance?active={address}"
            req = urllib.request.Request(url, headers={"User-Agent": "CorvusCorax/0.9"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if address in data:
                    return data[address].get("final_balance", 0) / 100000000.0  # satoshi → BTC
        except Exception:
            pass
        return None

    def execute(self):
        args = self.target or []
        if not args:
            return self.error("usage: wallet <address> [chain] [person]")

        address = args[0].strip()
        chain_hint = None
        person = None

        for arg in args[1:]:
            if arg.lower() in ("btc", "eth", "sol"):
                chain_hint = arg.lower()
            else:
                person = arg

        self.begin_investigation(
            goal="Wallet Intelligence Analysis",
            phases=[
                (1, "ADDRESS VALIDATION"),
                (2, "CHAIN DETECTION"),
                (3, "ENTITY MAPPING"),
            ],
        )

        # 1. Format doğrulama
        self.status_step(f"Validating address {address[:12]}...")
        chain = self._detect_chain(address)
        if not chain:
            return self.error(f"Invalid or unrecognized wallet address: {address}")
        if chain_hint and chain_hint != chain:
            return self.error(f"Address format suggests {chain}, but user specified {chain_hint}")

        # 2. Zincir tespiti
        self.status_step(f"Chain detected: {chain.upper()}")
        explorer_url = self._explorer_url(chain, address)

        # 3. Bakiye sorgusu (BTC için)
        balance = None
        if chain == "btc":
            def run_balance():
                return self._fetch_btc_balance(address)
            self.status_step("Querying BTC balance (blockchain.info)", work=run_balance)
            balance = self._fetch_btc_balance(address)

        # --- Varlık Kaydı ---
        wallet_props = {
            "chain": chain,
            "explorer_url": explorer_url,
            "balance_btc": balance,
        }
        self.add_wallet(address, chain, wallet_props)

        # --- Temporal Olaylar ---
        self.log_event("wallet_identified", entity=f"wallet:{address}",
                       metadata={"chain": chain, "explorer": explorer_url})
        if balance is not None:
            self.log_event("balance_queried", entity=f"wallet:{address}",
                           metadata={"balance_btc": balance})

        # --- İlişkiler ---
        self.add_relation(
            "wallet", address, "on_chain", "blockchain", chain,
            evidence=f"Address format matched {chain.upper()} ({explorer_url})",
            confidence=1.0,
        )

        # Kişiye aday bağlama (candidate — cüzdanlar paylaşılabilir)
        if person:
            self.add_person(person)
            self.add_relation(
                "person", person, "wallet_candidate_for", "wallet", address,
                evidence=f"User-provided association: {person} linked to wallet {address} as candidate",
                confidence=0.4,
            )
            self.log_event("wallet_candidate_for", entity=f"person:{person}",
                           metadata={"wallet": address, "chain": chain, "confidence": 0.4})

        self.add_note(
            f"Wallet {address} identified on {chain.upper()} chain"
            f"{f' — balance: {balance} BTC' if balance is not None else ''}",
            severity="info", confidence=0.9,
        )

        data = {
            "address": address,
            "chain": chain,
            "explorer_url": explorer_url,
            "balance_btc": balance,
            "person_candidate": person,
        }
        return self.success(target=address, data=data)