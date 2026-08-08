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

            if command == "context":
                if args and args[0] == "clear":
                    context.clear()
                    print("  [+] Intelligence context memory cleared.")
                elif args and args[0] == "--admiralty":
                    # Show admiralty intelligence details
                    print(context.get_admiralty_summary())
                elif args and len(args) >= 2 and args[1] == "--admiralty":
                    # Show admiralty details for specific entity
                    entity = args[0]
                    print(context.get_entity_admiralty(entity))
                else:
                    print(context.get_summary())
                continue

            if command not in modules:
                print(f"  Unknown command: '{command}'. Type 'help' to see available commands.")
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