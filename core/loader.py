import os
import sys
import importlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

MODULE_PATH = os.path.join(BASE_DIR, "modules")

def load_modules():
    modules = {}

    for file in os.listdir(MODULE_PATH):
        if file.endswith(".py") and not file.startswith("_"):
            module_name = file[:-3]

            module = importlib.import_module(f"modules.{module_name}")

            if hasattr(module, "name") and hasattr(module, "run"):
                modules[module.name] = module

    return modules