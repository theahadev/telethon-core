import importlib
import pkgutil
import types
from typing import List, Tuple

from loguru import logger

modules: List[Tuple[str, types.ModuleType]] = []

logger.debug(f"Starting module discovery in {__name__}")

for importer, module_name, ispkg in pkgutil.iter_modules(__path__):
    logger.debug(f"Loading module: {module_name} (package={ispkg})")
    try:
        module = importlib.import_module(f"{__name__}.{module_name}")
        modules.append((module_name, module))
        logger.debug(f"Successfully loaded module: {module_name}")
    except Exception as e:
        logger.error(f"Failed to load module {module_name}: {e}", exc_info=True)

logger.debug(f"Module discovery complete. Loaded {len(modules)} modules")
