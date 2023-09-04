import urltitle

from addict import Dict
from rich.console import Console

from .cookiejar import Cookiejar

excluded_urls = Dict(
    basic=["&uri=", "#uri="],
    parse=dict(
        # The Great Suspender
        tgs="chrome-extension://idmpfopopigkhhmehkcenekenbiicmej/html/snooze.html?url=",
    ),
    special=dict(
        # URL Prefix
        prefix="://",
        # Tiny Suspender Begining
        tsb="chrome-extension://bbomjaikkcabgmfaomdichgcodnaeecf/suspend.html?url=",
        # Tiny Suspender End
        tse="&title",
    ),
)

reader = urltitle.URLTitleReader(verify_ssl=True)
urltitle.config.NETLOC_OVERRIDES = Dict(urltitle.config.NETLOC_OVERRIDES)
cookiejar = Cookiejar(Cookiejar.paths)

console = Console(stderr=True)
