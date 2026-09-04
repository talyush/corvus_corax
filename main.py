import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from core.loader import load_modules
from core.banner import show_banner
from core.config import load_config
from core.logger import get_logger
from core.context import ContextManager
from output.output_manager import OutputManager

from core.analyst_advisor import AnalystAdvisor

config = load_config()
logger = get_logger()
modules = load_modules()
context = ContextManager()
output = OutputManager(logger, mode=config.get("output_mode", "text"))
advisor = AnalystAdvisor(context)

show_banner()
logger.info("Corvus started.")


def run_module(command, args):
    module_class = modules[command]
    module = module_class(target=args, config=config, logger=logger, context=context)
    return module.execute()


def print_output(payload):
    output.clear()
    output.add_result(payload)
    print(output.to_text())
    output.to_log()


def exit_animation():
    """Corvus exit animasyonu."""
    C_MAGENTA = "\033[35m"
    C_BOLD    = "\033[1m"
    C_DIM     = "\033[2m"
    C_RESET   = "\033[0m"
    msg = "The crow returns to the shadows..."
    print()
    print(f"  {C_MAGENTA}{C_BOLD}", end="", flush=True)
    for ch in msg:
        print(ch, end="", flush=True)
        time.sleep(0.04)
    print(f"{C_RESET}")
    print(f"  {C_DIM}Session ended. Stay unseen.{C_RESET}")
    print()


def main():
    while True:
        try:
            cmd_input = input("corvus > ").strip()
            if not cmd_input:
                continue

            parts = cmd_input.split()
            command = parts[0].lower()
            args = parts[1:]

            if command in ("exit", "quit"):
                exit_animation()
                break

            if command == "vault":
                # v0.9: Intelligence Vault — kalıcı istihbarat kasası
                from core.db import IntelligenceVault
                from core.config import load_rules as _load_rules
                _rules = _load_rules()
                _vault_dir = _rules.get("pol", {}).get("vault_dir", "vault")
                vault = IntelligenceVault(_vault_dir)

                if args and args[0] == "show":
                    stats = vault.stats()
                    print("=" * 60)
                    print("INTELLIGENCE VAULT")
                    print("=" * 60)
                    print(f"  Vault Directory : {stats['vault_dir']}")
                    print(f"  Events Stored   : {stats['event_count']}")
                    print(f"  Entities Indexed: {stats['entity_count']}")
                    print(f"  State Exists    : {stats['state_exists']}")
                    print(f"  Evidence Files  : {stats['evidence_files']}")
                    print("=" * 60)
                elif args and args[0] == "events" and len(args) >= 2:
                    entity = args[1]
                    events = vault.query_events(entity=entity, limit=50)
                    print(f"  Vault events for {entity}: {len(events)}")
                    for ev in events[:20]:
                        ts = ev.get("timestamp", "")[11:19]
                        action = ev.get("action", "?")
                        source = ev.get("source", "")
                        print(f"    [{ts}] {action} (src: {source})")
                elif args and args[0] == "confirm" and len(args) >= 2:
                    # Session'daki event'i kalıcı kanıta dönüştür
                    entity = args[1]
                    session_events = context.data.get("events", [])
                    confirmed = 0
                    for ev in session_events:
                        if entity in ev.get("entity", ""):
                            ok, _ = vault.confirm_event(ev)
                            if ok:
                                confirmed += 1
                    print(f"  [+] {confirmed} events confirmed to vault for {entity}")
                elif args and args[0] == "stats":
                    stats = vault.stats()
                    print(f"  Vault: {stats['event_count']} events, {stats['entity_count']} entities, {stats['evidence_files']} evidence files")
                else:
                    print("  Usage: vault <show|events <entity>|confirm <entity>|stats>")
                continue

            if command == "context":
                if args and args[0] == "clear":
                    context.clear()
                    print("  [+] Intelligence context memory cleared.")
                elif args and args[0] == "save" and len(args) >= 2:
                    # v0.9: Kalıcı depolama — The Machine hafızası
                    from core.db import save_state
                    ok, msg = save_state(context, args[1])
                    print(f"  [+] {msg}")
                elif args and args[0] == "save":
                    from core.db import save_state
                    ok, msg = save_state(context)
                    print(f"  [+] {msg}")
                elif args and args[0] == "load" and len(args) >= 2:
                    from core.db import load_state
                    ok, msg = load_state(context, args[1])
                    print(f"  [+] {msg}")
                elif args and args[0] == "load":
                    from core.db import load_state
                    ok, msg = load_state(context)
                    print(f"  [+] {msg}")
                elif args and args[0] == "--admiralty":
                    # Show admiralty intelligence details
                    print(context.get_admiralty_summary())
                elif args and len(args) >= 2 and args[1] == "--admiralty":
                    # Show admiralty details for specific entity
                    entity = args[0]
                    print(context.get_entity_admiralty(entity))
                elif args and args[0] == "--events":
                    # Temporal event stream (Pattern of Life altyapısı)
                    print(context.get_events_summary())
                elif args and len(args) >= 2 and args[1] == "--events":
                    # Belirli bir varlığın temporal olayları
                    entity = args[0]
                    print(context.get_events_summary(entity=entity))
                elif args and args[0] == "--entities":
                    # Entity registry özeti
                    entity_type = None
                    if len(args) >= 2 and not args[1].startswith("--"):
                        entity_type = args[1]
                    print(context.get_entities_summary(entity_type=entity_type))
                else:
                    print(context.get_summary())
                continue

            if command not in modules:
                # v1.1.1 Cognitive Interface Fallback: Route natural language to chat module
                result = run_module("chat", parts)
                print_output(result)
                continue

            result = run_module(command, args)
            print_output(result)
            advisor.print_suggestions()

        except KeyboardInterrupt:
            exit_animation()
            break
        except Exception as e:
            logger.error(f"CLI error: {e}")
            print(f"  [!] An error occurred: {e}")


if __name__ == "__main__":
    main()