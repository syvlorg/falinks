import json

from addict import Dict
from autoslot import Slots
from collections import defaultdict
from contextlib import contextmanager
from functools import partial
from pathvalidate import sanitize_filename, sanitize_filepath
from rich.pretty import pprint
from rich.progress import Progress, track
from time import sleep
from valiant import SuperPath, is_coll

from .link import Link
from .miscellaneous import to_json
from .variables import console, excluded_urls


class Falinks(Slots):
    def __init__(
        self,
        append=False,
        dedup=False,
        exclude=tuple(),
        export_any=False,
        export_json=False,
        export_links=False,
        ignore_favIconUrl=False,
        ignore_title=False,
        sites=False,
        sort=False,
        testing=False,
        verbose=False,
    ):
        self.count_files = dict()
        self.dedup = dedup
        self.exclude = {SuperPath(e) for e in exclude}

        self.testing = testing
        self.ignore_favIconUrl = self.testing or ignore_favIconUrl
        self.ignore_title = self.testing or ignore_title

        self.export_json = export_json
        self.export_links = export_links
        self.export_any = export_any or self.export_json or self.export_links

        self.link_dict = Dict()
        self.sites = sites
        self.sort = sort
        self.verbose = verbose

        self.append = append
        self.mode = ("a" if self.append else "w") + "+"

    @contextmanager
    def write_count_header(self, file):
        if self.verbose > 1:
            print(header := "File: " + str(file))
            print(sep := "=" * len(header))
            if (self.verbose > 2) and self.export_any:
                self.count_files[file] = open(
                    str(file.parent / ".falinks" / "counts" / file.stem) + ".txt", "w"
                )
                self.count_files[file].write(header + "\n" + sep + "\n")
        yield
        if self.verbose > 2:
            print()
            if self.export_any:
                self.count_files[file].write("\n")

    def print_file_header(self, file):
        if self.verbose > 1:
            print(header := "File:" + file)
            print("=" * len(header))

    def create(self, *files):
        for file in files:
            file = SuperPath(file, strict=True)
            if file.is_dir():
                self.create(file.iterdir())
            else:
                self._create(file)
                if self.sites:
                    self.site_create(file)
        else:
            return self.link_dict

    @contextmanager
    def progress(self, p=None):
        if p:
            yield p
        else:
            with Progress(console=console) as p:
                yield p

    def convert(self, links, progress=None, message=None):
        links = dict.fromkeys(links) if self.dedup else links
        Links = []
        with self.progress(progress) as p:
            converting = p.add_task(message or "Converting links...", total=len(links))
            # Answer From:
            # Answer: https://stackoverflow.com/a/17016257/10827766
            # User: https://stackoverflow.com/users/1219006/jamylak
            for link in links:
                if isinstance(link, Link):
                    Links.append(link)
                elif isinstance(link, dict):
                    Links.append(
                        Link(
                            link["url"],
                            title=link["title"],
                            favIconUrl=link["favIconUrl"],
                            ignore_favIconUrl=self.ignore_favIconUrl,
                            ignore_title=self.ignore_title,
                        )
                    )
                else:
                    Links.append(
                        Link(
                            link,
                            ignore_favIconUrl=self.ignore_favIconUrl,
                            ignore_title=self.ignore_title,
                        )
                    )
                p.update(converting, advance=1)
                sleep(0.005)
            return sorted(Links) if self.sort else Links

    @contextmanager
    def status(self, *args):
        if self.verbose == 0:
            yield console.status(*args)
        else:
            yield

    def track(self, links, **kwargs):
        if self.verbose == 0:
            return track(links, console=console, **kwargs)
        else:
            return links

    def site_create(self, file):
        def create_link_dict(progress, links, fetching):
            ld = dict()
            ld["default"] = []
            ld["http"] = defaultdict(list)
            ld["https"] = defaultdict(list)
            for line in links:
                if line:
                    prefix = excluded_urls.special.prefix
                    name = line[: line.find(prefix)] + prefix
                    sanitized_name = sanitize_filename(name.removesuffix(prefix))
                    if sanitized_name.startswith("http"):
                        ld[sanitized_name][
                            line.removeprefix(name).split("/")[0]
                        ].append(line.strip())
                    else:
                        ld["default"].append(line.strip())
                    progress.update(fetching, advance=1)
                    sleep(0.005)
            return ld

        def convert_link_dict(links, progress):
            ld = Dict()
            for [protocol, sites] in links.items():
                if sites:
                    if protocol == "default":
                        ld[protocol] = self.convert(
                            sites,
                            progress=progress,
                            message="Converting links under the default protocol...",
                        )
                    else:
                        for [site, links] in sites.items():
                            ld[protocol][site] = self.convert(
                                links,
                                progress=progress,
                                message=f'Converting links under the "{protocol}" protocol from {site}...',
                            )
            return ld

        def print_link_dict(links):
            for [protocol, sites] in links.items():
                if sites:
                    if protocol == "default":
                        if self.verbose > 1:
                            print(protocol + ":")
                        for link in sites:
                            print(link)
                        print()
                    else:
                        for [site, links] in sites.items():
                            if self.verbose > 1:
                                print(f"{protocol}://{site}:")
                            for link in links:
                                print(link)
                            print()
                    print()
                print()

        if not file in self.exclude:
            with Progress(console=console) as progress:
                cld = partial(create_link_dict, progress)
                if self.process == "session_buddy":
                    ld = dict()
                    for session, links in self.link_dict[file].items():
                        ld[session] = cld(
                            links,
                            progress.add_task(
                                f"Fetching links from session {session} in link dictionary...",
                                total=len(links),
                            ),
                        )
                    del self.link_dict[file]
                    for session, links in ld.items():
                        self.link_dict[file][session] = convert_link_dict(
                            links, progress
                        )
                    if self.verbose:
                        for session, links in self.link_dict[file].items():
                            print_link_dict(links)
                else:
                    self.link_dict[file] = convert_link_dict(
                        cld(
                            self.link_dict[file],
                            progress.add_task(
                                f"Fetching links from link dictionary...",
                                total=len(self.link_dict[file]),
                            ),
                        ),
                        progress,
                    )
                    if self.verbose:
                        print_link_dict(self.link_dict[file])

    def site_export(self):
        def inner(dir, protocols):
            for [protocol, sites] in protocols.items():
                if sites:
                    if protocol == "default":
                        self._export(dir / "default", sites, protocol)
                    else:
                        for [site, links] in sites.items():
                            self._export(
                                dir / protocol / site,
                                links,
                                site,
                            )

        if self.process == "session_buddy":
            for [file, sessions] in self.link_dict.items():
                with self.write_count_header(file):
                    for [session, protocols] in sessions.items():
                        # Answer From:
                        # Answer: https://stackoverflow.com/a/42288083/10827766
                        # User: https://stackoverflow.com/users/310399/js
                        inner(
                            file.parent
                            / ".falinks"
                            / self.process
                            / file.stem
                            / session,
                            protocols,
                        )
        else:
            for [file, protocols] in self.link_dict.items():
                with self.write_count_header(file):
                    # Answer From:
                    # Answer: https://stackoverflow.com/a/42288083/10827766
                    # User: https://stackoverflow.com/users/310399/js
                    inner(
                        file.parent / ".falinks" / self.process / file.stem, protocols
                    )

    # Answer From:
    # Answer: https://stackoverflow.com/a/59672132/10827766
    # User: https://stackoverflow.com/users/2907819/kmaork
    def _export(self, file, links, session):
        file = SuperPath(sanitize_filepath(file, platform="auto"))
        file.parent.mkdir(parents=True, exist_ok=True)
        if self.export_json:
            json_file = file.parent / (file.name + ".json")
            if self.append and json_file.exists():
                with json_file.open("r") as f:
                    tabs = to_json(
                        self.track(links, description=f"Dumping links to {file}..."),
                        file=f,
                    )
            else:
                tabs = to_json(
                    self.track(links, description=f"Dumping links to {file}..."),
                )
            with json_file.open("w") as f:
                json.dump(
                    tabs,
                    f,
                    indent=4,
                )
        if self.export_links:
            with (file.parent / (file.name + ".txt")).open(self.mode) as f:
                for link in self.track(
                    links, description=f"Writing links to {file}..."
                ):
                    f.write(link + "\n")
        if self.verbose > 2:
            count_string = f"{session}: {len(links)}"
            print(count_string)
            self.count_files[file].write(count_string + "\n")

    def export(self):
        for [file, links] in self.link_dict.items():
            with self.write_count_header(file):
                # Answer From:
                # Answer: https://stackoverflow.com/a/42288083/10827766
                # User: https://stackoverflow.com/users/310399/js
                self._export(
                    file.parent / ".falinks" / self.process / file.stem,
                    links,
                    file,
                )

    def create_and_export(self, *files):
        self.create(*files)
        if self.export_any:
            if self.sites:
                self.site_export()
            else:
                self.export()
