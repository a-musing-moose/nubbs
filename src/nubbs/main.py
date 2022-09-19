import cmd
from rich.console import Console
import typing as t

from .apps.welcome import Welcome


class NuBBS(cmd.Cmd):
    intro = "Welcome to the NuBBS shell. Type help or ? to list commands.\n"
    prompt = "(nu) "

    apps = (Welcome,)

    def __init__(
        self,
        completekey: str = "tab",
        stdin: t.IO[str] | None = None,
        stdout: t.IO[str] | None = None,
    ) -> None:
        self.console = Console(file=stdout)
        self.load_apps()
        super().__init__(completekey=completekey, stdin=stdin, stdout=stdout)

    def load_apps(self):
        for app in self.apps:
            setattr(self, f"do_{app.name}", app.as_callable(console=self.console))
            setattr(
                self,
                f"help_{app.name}",
                lambda: app(console=self.console).help(),
            )

    def get_names(self) -> list[str]:
        """
        Return an alphabetized list of names comprising the attributes of this instance

        The default implementation of this method performs `dir` on the _class_. Since
        we dynamically add commands this default approach does not work as the commands
        are added to an instance not the class.
        """
        return dir(self)

    def precmd(self, line: str) -> str:
        # Cmd turns Ctrl+d in the string "EOF", here we remap it to "exit"
        if line.strip() == "EOF":
            line = "exit"
        return super().precmd(line)

    def do_exit(self, line: str) -> bool:
        """
        Exits the shell
        """
        return True
