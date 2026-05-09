from core.module_base import BaseModule

class VersionModule(BaseModule):
    name = "version"
    
    def execute(self):
        return self.success(
            target="local",
            data={
                "name": "Corvus Corax",
                "version": "v0.4",
                "motto": "Seeing the unseen systems.",
            },
        )
