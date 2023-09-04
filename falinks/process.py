from rich.progress import Progress
from sh import wc
from time import sleep
from valiant import SuperPath

from .falinks import Falinks
from .variables import console


class Process(Falinks):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process = "processed"

    def _create(self, file):
        if not file in self.exclude:
            link_list = []
            with Progress(console=console) as progress, file.open() as f:
                fetching = progress.add_task(
                    f"Fetching links from {file}...",
                    total=int(wc(file, l=True).strip().split(" ")[0]),
                )
                for line in f:
                    if line:
                        link_list.append(line.strip())
                    progress.update(fetching, advance=1)
                    sleep(0.005)
                self.link_dict[file] = self.convert(
                    link_list,
                    progress=progress,
                    message=f"Converting links from {file}...",
                )
            if self.verbose:
                for link in self.link_dict[file]:
                    print(link)
                print()
