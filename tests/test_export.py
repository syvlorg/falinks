from falinks import Process, Telegram, SessionBuddy, resources
from falinks.miscellaneous import output_file
from filecmp import cmp
from functools import partial
from oreo import mark_apod
from os import sep
from pathlib import Path
from pytest import mark, param
from rich.pretty import pprint


class TestExport:
    @mark.parametrize(
        "process, source",
        (
            param(Process, "links.txt", marks=mark.process),
            param(Telegram, "telegram.json", marks=mark.telegram),
            param(SessionBuddy, "session_buddy.json", marks=mark.session_buddy),
            param(
                SessionBuddy,
                "session_buddy_processed.json",
                marks=mark.session_buddy,
            ),
        ),
    )
    @mark.parametrize(
        "opts",
        mark_apod(("dedup", "sites", "sort"), (True, False), lambda k, v: v),
    )
    @mark.parametrize(
        "ext",
        (
            param(
                "." + ext,
                marks=getattr(mark, ext),
            )
            for ext in ("txt", "json")
        ),
    )
    def test_links(self, ext, opts, tmpdir, process, source):
        CMP = partial(cmp, shallow=False)
        glob = "*" + ext
        output_file_name = output_file(**opts)
        p = process(
            export_json=ext == ".json",
            export_links=ext == ".txt",
            testing=True,
            **opts,
        )
        p.create_and_export(tmpdir / source)
        dot_falinks = tmpdir / ".falinks" / p.process
        dot_falinks_string = str(dot_falinks)
        if process == SessionBuddy:
            for file in dot_falinks.rglob(glob):
                assert CMP(
                    file,
                    Path(
                        resources,
                        "links",
                        "session_buddy",
                        output_file_name,
                        str(file).removeprefix(
                            dot_falinks_string + f"/{source.removesuffix(ext)}/"
                        ),
                    ),
                )
        else:
            if opts["sites"]:
                for file in dot_falinks.rglob(glob):
                    assert CMP(
                        file,
                        Path(
                            resources,
                            "links",
                            output_file_name,
                            str(file).removeprefix(
                                dot_falinks_string + f"/{source.removesuffix(ext)}/"
                            ),
                        ),
                    )
            else:
                for file in dot_falinks.rglob(glob):
                    assert CMP(
                        file,
                        Path(
                            resources,
                            "links",
                            output_file_name + ext,
                        ),
                    )
