#!/usr/bin/env python3
import rich.traceback as RichTraceback

RichTraceback.install(show_locals=True)

import hy

hy.macros.require(
    "falinks.__main__",
    # The Python equivalent of `(require falinks.__main__ *)`
    None,
    assignments="ALL",
    prefix="",
)
hy.macros.require_reader("falinks.__main__", None, assignments="ALL")
from falinks.__main__ import *
