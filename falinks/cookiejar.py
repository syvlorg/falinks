try:
    import rich_click as click
except ImportError:
    import click

import json
import urltitle
from addict import Dict
from pathlib import Path


class Cookiejar(Dict):
    types = (dict, str, click.Path, Path)
    paths = {
        site: Path.home() / ".local" / "falinks" / "cookies" / site
        for site in ("exhentai.org",)
    }
    names = {"exhentai.org": ("ipb_member_id", "ipb_pass_hash")}

    def __init__(self, *args, cookies=None, **kwargs):
        # Since this uses `__setitem__',
        # if I want to pass in `cookies' directly to initialize the `addict' instead,
        # I don't need to use `self.convert'
        super().__init__(*args, **kwargs)

        self.update(cookies or dict())

    # Adapted From:
    # Comment: https://stackoverflow.com/questions/3334809/python-urllib2-how-to-send-cookie-with-urlopen-request#comment44976935_3334959
    # User: https://stackoverflow.com/users/446610/greg-glockner
    def set(self, site):
        urltitle.config.NETLOC_OVERRIDES[site]["extra_headers"]["Cookie"] = "; ".join(
            (k + "=" + v for [k, v] in self[site].items())
        )

    def set_all(self):
        for site in self:
            self.set(site)

    def __setitem__(self, k, v):
        return super().__setitem__(k, self._convert(v))

    # Adapted From: https://peps.python.org/pep-0584/#reference-implementation
    def __or__(self, other):
        if not isinstance(other, Cookiejar.types):
            return NotImplemented
        new = Cookiejar(self)
        new.update(other)
        return new

    # Adapted From: https://peps.python.org/pep-0584/#reference-implementation
    def __ror__(self, other):
        if not isinstance(other, Cookiejar.types):
            return NotImplemented
        new = Cookiejar(other)
        new.update(self)
        return new

    # Adapted From: https://peps.python.org/pep-0584/#reference-implementation
    def __ior__(self, other):
        self.update(other)
        return self

    def _load(self, file):
        if file.exists():
            with file.open() as f:
                return json.load(f)

    def _convert(self, v):
        match v:
            case t if isinstance(t, dict):
                return v
            case t if isinstance(t, (str, click.Path)):
                return self._load(Path(v))
            case t if isinstance(t, Path):
                return self._load(v)
            case _:
                return NotImplemented

    def convert(self, other):
        return {k: self._convert(v) for [k, v] in other.items()}

    def update(self, other):
        for [k, v] in self.convert(other).items():
            self[k].update_(v)

    def update_(self, other):
        return super(Dict, self).update(other)
