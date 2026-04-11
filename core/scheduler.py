class Scheduler:
    def __init__(self, modules, logger=None):
    

        self.modules = modules
        self.logger = logger

    def run_all(self):
        results = []
        for module in self.modules:
            results.append(module.execute())
        return results