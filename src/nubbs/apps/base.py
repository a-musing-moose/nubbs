from rich.console import Console
import typing as t


class NuApp:

    name: str
    help_text: str

    def __init__(self, console: Console) -> None:
        self.console = console

    def do(self, line: str) -> bool | None:
        ...

    def help(self) -> str:
        help_text = getattr(self, "help_text", None)
        if help_text:
            self.console.print(self.help_text)
        else:
            self.console.print(
                f":warning:\tNo help text define for the [i]{self.name}[/i] app",
                style="red",
            )

    @classmethod
    def as_callable(cls, console: Console) -> t.Callable[[str], bool]:
        def _callable(line: str) -> bool:
            instance = cls(console)
            return instance.do(line)

        return _callable
