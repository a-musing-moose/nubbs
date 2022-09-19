import dataclasses

import invoke

# CONSTANTS

PACKAGE = "nubbs"


@invoke.task
def help(ctx):
    """
    Displays help text
    """
    ctx.run("inv -l", pty=True)


# Services


@invoke.task
def run_docs_server(ctx):
    """
    Runs the mkdocs developer server
    """
    title("Starting MkDocs documentation server")
    ctx.run("poetry run mkdocs serve -a localhost:8080")


@invoke.task
def run_services(ctx):
    """
    Run backing services with docker-compose
    """
    title("Starting backing services with Docker")
    ctx.run("docker-compose up")



# Quality Assurance


@invoke.task
def format(ctx):
    """
    Apply automatic code formating tools
    """
    title("Applying code formatters ")
    ctx.run("poetry run black src")
    ctx.run("poetry run isort src")


@invoke.task
def typing(ctx):
    """
    Check type annotations
    """
    title("Type checking")
    try:
        ctx.run(f"poetry run dmypy run -- src/{PACKAGE}")
    except invoke.exceptions.UnexpectedExit:
        print(
            "\n"
            "NOTE: mypy was run in daemon mode, which can lead to spurious\n"
            "errors when changing branches.\n"
            "If the errors observed do not make sense, or errors are occuring\n"
            "on known-good code run `inv typing-daemon-stop` to stop the\n"
            "dmypy daemon and run type checking again."
        )
        raise


@invoke.task
def typing_daemon_stop(ctx):
    """
    Stop the mypy typing daemon
    """
    title("Terminating type checking Daemon")
    ctx.run("poetry run dmypy stop")


@invoke.task
def lint(ctx):
    """
    Check linting in the src folder
    """
    title("Linting code")
    stdout_captured = []

    # Need to collect the `stdout` during the command run in order to check
    # for specific error messages in the output
    #
    # UnexpectedExit doesn't hold the stdout, and could capture stdout to a
    # stream, but then if stdout and stderr both output they will not interpolate
    # correctly
    class StreamInterceptor(invoke.watchers.StreamWatcher):
        def submit(self, stream):
            stdout_captured.append(stream)
            return (stream,)

    try:
        ctx.run("poetry run flake8 src tests", watchers=(StreamInterceptor(),))
    except invoke.exceptions.UnexpectedExit:
        stdout_text = "".join(stdout_captured)
        for error_code in ("BLK100", "I001", "I003", "I004", "I004"):
            if error_code in stdout_text:
                print(
                    "One or more formatting errors occurred. Please ensure you have run"
                    " `inv format` to autoformat the code"
                )
                break
        # By catching and raising the UnexpectedExit exception, the 'terminate on
        #  error' behaviour of invoke is preserved
        raise


@invoke.task
def security(ctx):
    """
    Check for potential vulnerabilities in packages
    """
    title("Running security checks")
    ctx.run("poetry run safety check --full-report")


@invoke.task(
    help={
        "name": "only run tests which match the keyword expression",
        "suite": "Only run tests in the named suite (system|functional)",
        "verbose": "run tests in verbose mode",
    }
)
def test(ctx, name="", verbose=False, suite=None):
    """
    Runs the test suite
    """

    title_suffix = "S"
    args = ["poetry run pytest"]
    if verbose:
        args.append("-vv")

    if suite:
        args += ["-m", suite]
        title_suffix = f" ({suite})"
    if name:
        args += ["--no-cov", "-sk", name]
    else:
        args += [
            f"--cov={PACKAGE}",
            "--cov-report=term",
            "--cov-report=xml",
            "--no-cov-on-fail",
            "--cov-context=test",
        ]

    args.append("tests")

    cmd = " ".join(args)

    title(f"Running the test suite{title_suffix}")
    ctx.run(cmd, pty=True)
    if "--cov" in cmd:
        ctx.run("poetry run coverage html --show-contexts")

@invoke.task(typing, test, lint, security)
def check(ctx):
    """
    Runs all the code checking tools
    """
    print("All checks completed successfully 🕺")


# Builds and Deployment

@invoke.task
def build(ctx, tag=None):
    """
    Build the service Docker image
    """
    title("Building Docker image 🐳")
    commit_hash = "N/A"
    commit_time = "N/A"

    if tag is None:
        data = _build_data(ctx)
        commit_hash = data.commit_hash
        commit_time = data.commit_time
        tag = data.tag

    ctx.run(
        "docker build "
        f"--build-arg COMMIT_HASH={commit_hash} "
        f"--build-arg COMMIT_TIME={commit_time} "
        f"-t {PACKAGE}:{tag} ."
    )


@invoke.task
def build_docs(ctx):
    """
    Build the Codon documentation
    """
    title("Building documentation")
    ctx.run("poetry run mkdocs build")


# Helper Functions


@dataclasses.dataclass
class BuildData:

    MAX_TAG_LENGTH = 128

    branch: str
    commit_hash: str
    commit_time: str

    @property
    def tag(self) -> str:
        max_branch_length = self.MAX_TAG_LENGTH - -(
            len(self.commit_hash) + len(self.commit_time) + 2
        )  # 2 for the hyphens
        return "-".join(
            [self.commit_time, self.branch[:max_branch_length], self.commit_hash]
        )


def _build_data(ctx) -> BuildData:
    """
    Retrieves the current git branch, commit hash and commit time for using during builds

    Also provides a `tag` which is suitable for use as a Docker image tag based on these values
    """
    max_tag_length = 128
    branch = ctx.run("git rev-parse --abbrev-ref HEAD", hide="stdout").stdout.strip()
    branch = (
        branch[:max_tag_length]
        .replace("/", "-")
        .encode("ascii", "ignore")
        .decode("ascii")
    )

    commit_hash = ctx.run("git rev-parse --short=12 HEAD", hide="stdout").stdout.strip()
    commit_time = ctx.run("git show -s --format=%ct", hide="stdout").stdout.strip()
    return BuildData(branch=branch, commit_hash=commit_hash, commit_time=commit_time)


def title(text):
    print(f"== {text.upper()} ==")
