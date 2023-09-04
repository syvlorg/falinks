import json

from falinks import Process, resources
from filecmp import cmp
from pytest import mark, param
from rich.pretty import pprint


@mark.process
@mark.append
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
def test_append(tmpdir, ext):
    p = Process(
        append=True,
        export_json=ext == ".json",
        export_links=ext == ".txt",
        testing=True,
    )
    links = (resources / "links" / "links.txt").read_text().strip().split("\n")
    index = int(len(links) / 2)
    split = tmpdir / "split.txt"
    split.write_text("\n".join(links[:index]))
    p.create_and_export(split)
    split.write_text("\n".join(links[index:]))
    p.create_and_export(split)
    assert cmp(
        tmpdir / ".falinks" / "processed" / ("split" + ext),
        resources / "links" / ("processed" + ext),
        shallow=False,
    )
