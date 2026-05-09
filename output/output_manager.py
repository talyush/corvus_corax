import json

class OutputManager:
    def __init__(self, logger=None, mode="text"):
        self.results = []
        self.logger = logger
        self.mode = (mode or "text").lower()

    def add_result(self, result):
        if result is None:
            return
        self.results.append(result)

    def clear(self):
        self.results.clear()

    def to_text(self):
        if not self.results:
            return ""
        if self.mode == "json":
            return json.dumps(self.results, ensure_ascii=False)
            
        output_str = ""
        for res in self.results:
            if isinstance(res, dict) and "data" in res:
                data = res["data"]
                if isinstance(data, str):
                    output_str += data + "\n"
                else:
                    output_str += json.dumps(data, indent=2, ensure_ascii=False) + "\n"
            else:
                output_str += json.dumps(res, indent=2, ensure_ascii=False) + "\n"
        return output_str.strip()

    def to_log(self):
        if not self.logger:
            return
        for r in self.results:
            self.logger.info(json.dumps(r, ensure_ascii=False))