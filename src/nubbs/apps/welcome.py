from .base import NuApp


class Welcome(NuApp):

    name = "welcome"
    help_text = "Hello?"

    def do(self, line: str) -> bool:
        self.console.print("welcome :wave:")
        return False
