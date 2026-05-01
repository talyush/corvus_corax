class BaseModule:
    name = "base"

    def __init__(self, target=None, config=None, logger=None, context=None):
        self.target = target
        self.config = config
        self.logger = logger
        self.context = context

    def execute(self):
        raise NotImplementedError("Module must implement execute()")

    def success(self, target="local", data=None):
        """Return a normalized success payload for all modules."""
        return {
            "module": self.name,
            "target": target,
            "status": "success",
            "data": data,
        }

    def error(self, message, target="local"):
        """Return a normalized error payload for all modules."""
        return {
            "module": self.name,
            "target": target,
            "status": "error",
            "error": str(message),
        }

# 🔥 GERİYE UYUMLULUK (çok önemli)
Module = BaseModule