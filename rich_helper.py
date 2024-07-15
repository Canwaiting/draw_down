import sys
from rich.console import Console
from functools import wraps
import time
from datetime import datetime
from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn


class RichHelper:
    _instance = None  # Class-level attribute to store the single instance

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RichHelper, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # To prevent reinitialization
            self.console = Console()
            self.log = self.Logger(self.console)
            self.initialized = True  # Mark as initialized

    def with_status(self, spinner_name='line', status_text='[bold white]正在处理中...[/bold white]', spinner_style='bold white'):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.console.status(status_text, spinner=spinner_name, spinner_style=spinner_style):
                    result = func(*args, **kwargs)
                    sys.stdout.flush()
                    return result
            return wrapper
        return decorator

    def with_progress_bar(self, total=100, description='Processing...', bar_format="{task.description} [{task.completed}/{task.total}]"):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with Progress(
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
                    TimeRemainingColumn(),
                    expand=True,
                ) as progress:
                    task = progress.add_task(description, total=total)
                    for i in range(total):
                        result = func(*args, **kwargs)
                        progress.advance(task)
                    sys.stdout.flush()
                    return result
            return wrapper
        return decorator

    def yellow(self,message):
        return f"[bold yellow]{message}[/bold yellow]"

    def white(self,message):
        return f"[bold white]{message}[/bold white]"



    class Logger:
        def __init__(self, console):
            self.console = console

        def _timestamp(self):
            return f"[bold white]{datetime.now().strftime('[%H:%M:%S]')}[/bold white]"

        def success(self, message, *args, **kwargs):
            self.console.print(f"{self._timestamp()} [bold white]{message}[/bold white]", *args, **kwargs)

        def info(self, message, *args, **kwargs):
            self.console.print(f"{self._timestamp()} [bold white]{message}[/bold white]", *args, **kwargs)

        def warn(self, message, *args, **kwargs):
            self.console.print(f"{self._timestamp()} [bold yellow]{message}[/bold yellow]", *args, **kwargs)

        def error(self, message, *args, **kwargs):
            self.console.print(f"{self._timestamp()} [bold red]{message}[/bold red]", *args, **kwargs)