class BaseModule:
    name = "base"

    def __init__(self, target=None, config=None, logger=None, context=None):
        self.target = target
        self.config = config
        self.logger = logger
        self.context = context

    def execute(self):
        raise NotImplementedError("Module must implement execute()")

# 🔥 GERİYE UYUMLULUK (çok önemli)
Module = BaseModule