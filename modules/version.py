from core.module_base import BaseModule

class VersionModule(BaseModule):
    name = "version"
    
    def execute(self):
        self.add_note("Version information queried", severity="info")
        return self.success(
            target="local",
            data={
                "name": "Corvus Corax",
                "version": "v0.6-nexus-core",
                "motto": "Seeing the unseen systems.",
            },
        )
