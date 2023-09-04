import json

from collections import defaultdict
from inflect import engine
from pathvalidate import sanitize_filename

from .falinks import Falinks
from .link import Link

e = engine()


class SessionBuddy(Falinks):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process = "session_buddy"

    def _create(self, file):
        ld = defaultdict(list)
        if not file in self.exclude:
            with file.open() as f:
                sessions = json.load(f)["sessions"]
                for session in sessions:
                    name = sanitize_filename(session.get("name", "default"))
                    for index, window in enumerate(session["windows"]):
                        for tab in self.track(
                            window["tabs"],
                            description=f'Fetching links from {e.ordinal(index)} window of session "{name}" in {file}...',
                        ):
                            ld[name].append(
                                Link(
                                    tab["url"],
                                    title=tab.get("title", None),
                                    favIconUrl=tab.get("favIconUrl", None),
                                    ignore_favIconUrl=self.ignore_favIconUrl,
                                    ignore_title=self.ignore_title,
                                )
                            )
            self.link_dict[file] = {
                session: self.convert(
                    links,
                    message=f'Converting links from session "{session}" in {file}...',
                )
                for [session, links] in ld.items()
            }
            if self.verbose:
                for [name, links] in self.link_dict[file].items():
                    if self.verbose > 1:
                        print(name + ":")
                    for link in links:
                        print(link)
                    print()
                print()

    def export(self):
        for [file, sessions] in self.link_dict.items():
            with self.write_count_header(file):
                for [session, links] in sessions.items():
                    if links:
                        # Answer From:
                        # Answer: https://stackoverflow.com/a/42288083/10827766
                        # User: https://stackoverflow.com/users/310399/js
                        self._export(
                            file.parent
                            / ".falinks"
                            / self.process
                            / file.stem
                            / session,
                            links,
                            session,
                        )
