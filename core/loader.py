import os
import importlib
from core.module_base import BaseModule
from core.logger import get_logger

logger = get_logger()

def load_modules():
    modules = {}
    module_dir = "modules"

    for file in os.listdir(module_dir):
        if not file.endswith(".py") or file.startswith("_"):
            continue

        module_name = file[:-3]

        try:
            # 🔥 DOĞRU IMPORT
            mod = importlib.import_module(f"{module_dir}.{module_name}")

            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)

                if isinstance(attr, type) and issubclass(attr, BaseModule) and attr is not BaseModule:
                    if attr.name in modules:
                        logger.warning(f"Duplicate module name: {attr.name}, skipping")
                        continue

                    modules[attr.name] = attr
                    logger.info(f"Module loaded: {attr.name}")

        except Exception as e:
            logger.error(f"Failed to load {module_name}: {e}")

    return modules