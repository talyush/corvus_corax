import time
import sys
from colorama import Fore, Style, init


class _PhaseContext:
    def __init__(self, session, index, label):
        self.session = session
        self.index = index
        self.label = label

    def __enter__(self):
        self.session._open_phase(self.index, self.label)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session._close_phase(success=exc_type is None)
        return False


class InvestigationSession:
    """
    Live investigation UI — goal header, phased progress, analyst commentary.
    Steps show RUNNING while work executes, then flip to OK.
    """

    def __init__(self, module_name, goal, phases, analyst_runtime=None):
        self.module_name = module_name
        self.goal = goal
        self.phases = list(phases)
        self.runtime = analyst_runtime
        self._phase_open = False
        self._started = False
        init(autoreset=True)

    def begin(self):
        if self._started:
            return self
        self._started = True
        print()
        bar = "=" * 62
        print(f"  {Fore.CYAN}{Style.BRIGHT}{bar}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}{Style.BRIGHT}  INVESTIGATION GOAL{Style.RESET_ALL}")
        print(f"  {Fore.WHITE}{self.goal}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}{Style.BRIGHT}{bar}{Style.RESET_ALL}")

        if self.runtime:
            for msg in self.runtime.preflight():
                self.analyst(msg, prefix="Context")
        print()
        return self

    def phase(self, index):
        if isinstance(index, str):
            try:
                index = self.phases.index(index)
            except ValueError:
                index = 0
        label = self.phases[index]
        return _PhaseContext(self, index, label)

    def run_step(self, message, work=None, analyst=None):
        """Show RUNNING, execute work, mark OK (or FAIL)."""
        label = message[:52]
        dots = "." * max(1, 32 - len(label))
        running = f"    {Fore.BLUE}[~]{Style.RESET_ALL} {message} {Fore.BLACK}{Style.DIM}{dots}{Style.RESET_ALL}"
        print(running, end="", flush=True)

        result = None
        error = None
        try:
            if work is not None:
                result = work()
        except Exception as exc:
            error = exc

        if error:
            print(f" [{Fore.RED}{Style.BRIGHT}FAIL{Style.RESET_ALL}]")
            raise error

        print(f" [{Fore.GREEN}{Style.BRIGHT}OK{Style.RESET_ALL}]")

        if analyst:
            if isinstance(analyst, (list, tuple)):
                for line in analyst:
                    self.analyst(line)
            else:
                self.analyst(analyst)
        return result

    def analyst(self, message, prefix="Analyst"):
        print(f"    {Fore.YELLOW}[{prefix}]{Style.RESET_ALL} {message}")

    def finish(self, summary=None):
        if summary:
            print(f"  {Fore.GREEN}{Style.BRIGHT}[+] {summary}{Style.RESET_ALL}")
        else:
            print(
                f"  {Fore.GREEN}{Style.BRIGHT}[+] Investigation complete -- synthesizing results{Style.RESET_ALL}"
            )
        print()
        sys.stdout.flush()

    def _open_phase(self, index, label):
        total = len(self.phases)
        print(f"  {Fore.MAGENTA}{Style.BRIGHT}>> Phase {index + 1}/{total} -- {label}{Style.RESET_ALL}")

    def _close_phase(self, success=True):
        if not success:
            print(f"    {Fore.RED}[!] Phase aborted{Style.RESET_ALL}")
        print()
