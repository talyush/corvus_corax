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

    # -------------------------
    # CLI FRIENDLY TEXT OUTPUT
    # -------------------------
    def to_text(self):
        lines = []

        for r in self.results:
            status = r.get("status", "unknown").upper()
            module = r.get("module", "unknown")
            target = r.get("target", "N/A")

            lines.append(f"[{module.upper()}] {status}")
            lines.append(f"Target: {target}")

            if status == "SUCCESS":
                data = r.get("data", "")
                lines.append("Result:")
                lines.append(str(data))

            else:
                lines.append("Error:")
                lines.append(r.get("error", "Unknown error"))

            lines.append("-" * 35)

        return "\n".join(lines)

    # -------------------------
    # JSON OUTPUT
    # -------------------------
    def to_json(self):
        return json.dumps(self.results, indent=4)

    # -------------------------
    # LOG OUTPUT
    # -------------------------
    def to_log(self):
        if not self.logger:
            return

        for r in self.results:
            self.logger.info(json.dumps(r))

    # -------------------------
    # FUTURE REPORT EXPORT
    # -------------------------
    def export_json(self, filename="report.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=4)