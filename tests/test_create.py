import json

from falinks import Process, Telegram, SessionBuddy, resources
from falinks.miscellaneous import to_json, output_file
from oreo import mark_apod
from pytest import mark, param
from rich.pretty import pprint


class TestCreate:
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
        mark_apod(("dedup", "sites", "sort"), (True, False)),
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
    def test_links(self, ext, opts, process, source, tmpdir):
        def inner(links):
            file = output_file(**opts)
            if opts["sites"]:
                for protocol in ("default", "http", "https"):
                    pfile = resources / "links" / file / protocol
                    pprop = links[protocol]
                    if protocol == "default":
                        if (resource := pfile.with_suffix(ext)).exists():
                            match ext:
                                case ".txt":
                                    assert (
                                        resource.read_text().strip().split("\n")
                                        == pprop
                                    )
                                case ".json":
                                    with resource.open() as f:
                                        assert json.load(f) == to_json(pprop)
                    else:
                        match ext:
                            case ".txt":
                                for file in pfile.rglob("*" + ext):
                                    assert (
                                        file.read_text().strip().split("\n")
                                        == pprop[file.stem]
                                    )
                            case ".json":
                                for file in pfile.rglob("*" + ext):
                                    with file.open() as f:
                                        assert json.load(f) == to_json(pprop[file.stem])
            else:
                file = resources / "links" / file
                file = file.parent / (file.name + ext)
                match ext:
                    case ".txt":
                        assert file.read_text().strip().split("\n") == links
                    case ".json":
                        with file.open() as f:
                            assert json.load(f) == to_json(links)

        tmpfile = tmpdir / source
        link_dict = process(testing=True, **opts).create(tmpfile)[tmpfile]
        if process == SessionBuddy:
            for links in link_dict.values():
                inner(links)
        else:
            inner(link_dict)
