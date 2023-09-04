import json

from rich.pretty import pprint

from .falinks import Falinks
from .link import Link


class Telegram(Falinks):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process = "telegram"

    def _create(self, file):
        if not file in self.exclude:
            link_list = []
            with file.open() as f:
                chat = json.load(f)
                for message in chat["messages"]:
                    if isinstance((texts := message["text"]), list):
                        for m in self.track(
                            texts,
                            description=f'Fetching links from chat "{chat["name"]}" in {file}...',
                        ):
                            if (
                                isinstance(m, dict)
                                and m["type"] == "link"
                                # NOTE: In order to check for the forward slash,
                                #       we need to ensure that the link is decoded.
                                and (
                                    "/"
                                    in (
                                        text := Link(
                                            m["text"],
                                            ignore_favIconUrl=self.ignore_favIconUrl,
                                            ignore_title=self.ignore_title,
                                        )
                                    )
                                )
                            ):
                                link_list.append(text)
            self.link_dict[file] = self.convert(
                link_list,
                message=f"Converting links from telegram chat backup {file}...",
            )
            if self.verbose:
                for link in self.link_dict[file]:
                    print(link)
                print()
