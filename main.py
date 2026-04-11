import core.config

print("CONFIG DOSYASI:", core.config.__file__)

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# -------------------------------
# PATH & CORE IMPORTS
# -------------------------------
sys.path.insert(0, os.path.dirname(__file__))

from core.loader import load_modules
from core.banner import show_banner
from core.config import load_config
from core.logger import get_logger
from core.scheduler import Scheduler
from core.context import ContextManager
import importlib.util
import os

output_path = os.path.join(os.path.dirname(__file__), "output", "output_manager.py")

spec = importlib.util.spec_from_file_location("output_manager", output_path)
output_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(output_module)

OutputManager = output_module.OutputManager

# -------------------------------
# CONFIG & LOGGER
# -------------------------------
config = load_config()
logger = get_logger()
logger.info(f"Log level from config: {config.get('log_level', 'INFO')}")

# -------------------------------
# MODULES & SCHEDULER
# -------------------------------
modules_dict = load_modules()  # dict {name: module_class}
modules_list = list(modules_dict.values())  # scheduler için liste

scheduler = Scheduler(modules_list, logger)

# -------------------------------
# OUTPUT MANAGER & CONTEXT
# -------------------------------
output = OutputManager(logger)
context = ContextManager()

# -------------------------------
# SHOW BANNER
# -------------------------------
show_banner()

# -------------------------------
# CLI LOOP
# -------------------------------
def main():
    while True:
        try:
            cmd_input = input("corvus > ").strip()
            if not cmd_input:
                continue

            cmd = cmd_input.split()
            command = cmd[0]

            if command == "exit":
                print("Exiting Corvus.")
                break

            elif command == "context":
                print("\n[+] Mevcut Recon Zihni (Context):")
                print(context.get_summary())
                continue

            elif command in modules_dict:
                # modül sınıfını instance olarak oluştur
                module_class = modules_dict[command]
                module_instance = module_class(target=cmd[1:], config=config, logger=logger, context=context)

                # execute wrapper ile çalıştır
                result = module_instance.execute()
                output.add_result(result)

                # terminal ve log çıktısı
                print(output.to_text())
                output.to_log()
                output.results.clear()

            else:
                print("Unknown command. Type 'help'.")

        except KeyboardInterrupt:
            print("\nExiting Corvus.")
            break
        except Exception as e:
            logger.error(f"CLI error: {e}")

if __name__ == "__main__":
    main()