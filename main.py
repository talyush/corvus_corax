import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from core.loader import load_modules
from core.banner import show_banner
from core.config import load_config
from core.logger import get_logger
from core.context import ContextManager
from output.output_manager import OutputManager

config = load_config()
logger = get_logger()
modules = load_modules()
context = ContextManager()
output = OutputManager(logger)

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
                print("Exiting Corvus.")
                break

            if command == "context":
                print(context.get_summary())
                continue

            if command not in modules:
                print("Unknown command. Type 'help'.")
                continue

            print(f"[*] Running module: {command}")
            result = run_module(command, args)
            print(f"[+] Module finished: {command}")
            print_output(result)

        except KeyboardInterrupt:
            print("\nExiting Corvus.")
            break
        except Exception as e:
            logger.error(f"CLI error: {e}")


if __name__ == "__main__":
    main()