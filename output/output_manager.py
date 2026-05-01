import json

class OutputManager:
    def __init__(self, logger=None):
        self.results = []
        self.logger = logger

    def add_result(self, result):
        if result is None:
            return
        self.results.append(result)

    def clear(self):
        self.results.clear()

    def to_text(self):
        if not self.results:
            return "[]"
        return json.dumps(self.results, indent=2, ensure_ascii=False)

    def to_log(self):
        if not self.logger:
            return
        for r in self.results:
            self.logger.info(json.dumps(r, ensure_ascii=False))