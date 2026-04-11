import json

print("OUTPUT MANAGER YÜKLENDİ")

class OutputManager:
    def __init__(self, logger=None):
        print("OUTPUT INIT ÇALIŞTI")
        self.results = []
        self.logger = logger

    def add_result(self, result):
        self.results.append(result)

    def to_text(self):
        return str(self.results)

    def to_log(self):
        if not self.logger:
            return
        for r in self.results:
            self.logger.info(str(r))