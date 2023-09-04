import favicon
import json
import requests
import urllib.parse

from autoslot import SlotsMeta
from bs4 import BeautifulSoup
from contextlib import contextmanager
from functools import partial
from requests.exceptions import HTTPError
from rich.pretty import pprint
from time import sleep
from urllib.request import urlopen
from urltitle import URLTitleError
from valiant import Confirm
from xxhash import xxh64

from .cookiejar import Cookiejar
from .variables import excluded_urls, cookiejar, reader


class MetaLink(SlotsMeta):
    def __init__(cls, *args, **kwargs):
        cls.e_counter = 0
        cls.danbooru_counter = 0


class Link(metaclass=MetaLink):
    def __init__(
        self,
        link,
        title=None,
        favIconUrl=None,
        ignore_favIconUrl=False,
        ignore_title=False,
    ):
        self.provided_title = title
        self.provided_favIconUrl = favIconUrl
        self.ignore_favIconUrl = ignore_favIconUrl
        self.ignore_title = ignore_title
        self.all_favicons = dict()
        self.safe = "!"
        self.link = link
        self.and_indices = [i for [i, c] in enumerate(self.link) if c == "&"]
        self.exhentai = False
        self.e_hentai = False
        self.url = self.parse()
        self.e621 = "e621.net/" in self.url
        self.rule_paheal = "paheal.net/" in self.url
        self.rule_xxx = "rule34.xxx/" in self.url
        self.imagefap = self.url.startswith("https://www.imagefap.com/")
        self.sessionBuddy = self.url.startswith(
            "chrome-extension://edacconmaakjimmfgnblocblbcdcpbko/"
        )
        self.twitter = any(
            (
                self.url.startswith(prefix)
                for prefix in ["https://twitter.com/", "https://mobile.twitter.com/"]
            )
        )

    def removeprefix(self, prefix):
        return self.url.removeprefix(prefix)

    def strip(self, chars=None):
        return self.url.strip(chars)

    def find(self, string, start=None, stop=None):
        return self.url.find(string, start, stop)

    def __contains__(self, key):
        return key in self.url

    def __hash__(self):
        return xxh64(self.url).intdigest()

    def __getitem__(self, item):
        return self.url[item]

    def __add__(self, summand):
        return self.url + str(summand)

    def __str__(self):
        return self.url

    def __repr__(self):
        return self.url

    def __lt__(self, link):
        if isinstance(link, Link):
            return self.url < link.url
        else:
            return self.url < link

    def __le__(self, link):
        if isinstance(link, Link):
            return self.url <= link.url
        else:
            return self.url <= link

    def __gt__(self, link):
        if isinstance(link, Link):
            return self.url > link.url
        else:
            return self.url > link

    def __ge__(self, link):
        if isinstance(link, Link):
            return self.url >= link.url
        else:
            return self.url >= link

    def __eq__(self, link):
        if isinstance(link, Link):
            return self.url == link.url
        else:
            return self.url == link

    def parse(self):
        link = self.link
        if link.startswith("chrome-extension://"):
            for prefix in excluded_urls.basic:
                if prefix in link:
                    # Adapted From:
                    # Answer: https://stackoverflow.com/a/33141629/10827766
                    # User: https://stackoverflow.com/users/2867928/mazdak
                    link = link[link.find(prefix) :].removeprefix(prefix)

            for prefix in excluded_urls.parse.values():
                if link.startswith(prefix):
                    # Adapted From:
                    # Answer: https://stackoverflow.com/a/33141629/10827766
                    # User: https://stackoverflow.com/users/2867928/mazdak
                    link = link[link.find(prefix) :].removeprefix(prefix)

            if link.startswith((prefix := excluded_urls.special.tsb)):
                # Adapted From:
                # Answer: https://stackoverflow.com/a/33141629/10827766
                # User: https://stackoverflow.com/users/2867928/mazdak
                link = link[
                    link.find(prefix) : link.find(excluded_urls.special.tse)
                ].removeprefix(prefix)

        while "%" in link:
            link = urllib.parse.unquote(link)
        if link.startswith("https://asstr.xyz/"):
            link = link.replace("https://asstr.xyz/", "https://asstr.org/")
        self.exhentai = link.startswith("https://exhentai.org/")
        self.e_hentai = self.exhentai or link.startswith("https://e-hentai.org/")
        if self.e_hentai:
            if "?f_search=" in link and link.count(":") == 1:
                for [k, v] in {"?f_search=": "tag/", '"': "", "$": ""}.items():
                    link = link.replace(k, v)
        return link

    def get(self, prop, func):
        prop = "&" + prop + "="
        if prop in self.link:
            index = self.link.find(prop)
            return urllib.parse.unquote(
                self.link[
                    index : self.and_indices[self.and_indices.index(index) + 1]
                ].removeprefix(prop)
            )
        else:
            return func()

    def faviconsToDict(self, favicons):
        favicon_dict = dict()
        for icon in favicons:
            if (icon.format not in favicon_dict) or (
                (icon.format in favicon_dict)
                and (icon.height > favicon_dict[icon.format][1])
            ):
                favicon_dict[icon.format] = (icon.url, icon.height)
        return {k: v[0] for k, v in favicon_dict.items()}

    @property
    def favIconUrl(self):
        if self.provided_favIconUrl:
            return self.provided_favIconUrl
        else:
            root_list = self.url.split("/")[:3]

            def inner():
                try:
                    prop = self.get(
                        "favIconUrl",
                        partial(favicon.get, self.url, timeout=20),
                    )
                    if isinstance(prop, list):
                        favicon_dict = self.faviconsToDict(prop)
                        for format in order:
                            if format in favicon_dict:
                                return favicon_dict[format]
                    else:
                        return prop
                except HTTPError:
                    # Adapted From:
                    # Answer: https://stackoverflow.com/a/55857894
                    # User: https://stackoverflow.com/users/428806/joshua-stafford
                    for link in (
                        "/".join(root_list + [file])
                        for file in (
                            # Adapted From: https://en.wikipedia.org/wiki/Favicon#How_to_use
                            "image.svg",
                            "image.png",
                            "image.gif",
                            "image.ico",
                            "myicon.ico",
                            "favicon.ico",
                        )
                    ):
                        try:
                            # Adapted From:
                            # Answer: https://stackoverflow.com/a/1949360
                            # User: https://stackoverflow.com/users/166712/anthony-forloney
                            if urlopen(link).getcode() == 200:
                                return link
                        except HTTPError as e:
                            if "HTTP Error 404: Not Found" in str(e):
                                pass
                            else:
                                raise HTTPError from e

            order = [
                "svg",
                "png",
                "gif",
                "ico",
            ]
            if self.sessionBuddy:
                return "https://cdn.jsdelivr.net/gh/syvlorg/falinks@main/falinks/resources/icons/session_buddy_favicon_32x32.png"
            else:
                if (root := "/".join(root_list)) not in self.all_favicons:
                    self.all_favicons[root] = inner()
                return self.all_favicons[root]

    @contextmanager
    def notify(self, message):
        filling = "# " + " " * len(message) + " #"
        border = "##" + "#" * len(message) + "##"
        print()
        print(border)
        print(filling)
        print("# " + message + " #")
        print(filling)
        print(border)
        print()
        yield

    # Adapted From: https://github.com/mikf/gallery-dl/blob/master/gallery_dl/extractor/exhentai.py#L82
    #               https://github.com/mikf/gallery-dl/blob/master/gallery_dl/extractor/common.py#L228
    def dump_exhentai_cookies(self):
        exhentai = "exhentai.org"
        url = "https://forums.e-hentai.org/index.php?act=Login&CODE=01"
        headers = dict(Referer="https://e-hentai.org/bounce_login.php?b=d&bt=1-1")
        prompt_prefix = 'Please enter your "ExHentai.org" / "E-Hentai Galleries"'
        data = dict(
            CookieDate="1",
            b="d",
            bt="1-1",
            UserName=(prompt_prefix + "username:").getuser(),
            PassWord=(prompt_prefix + "password:").getpass(),
            ipb_login_submit="Login!",
        )
        session = requests.session()
        response = session.request("POST", url, headers=headers, data=data)
        if b"You are now logged in as:" in response.content:
            with self.notify("You have been successfully logged in to ExHentai.org!"):
                cookies = {
                    cookie: response.cookies[cookie]
                    for cookie in Cookiejar.names[exhentai]
                }
                cookiejar.update({exhentai: cookies})

                # Adapted From:
                # Answer: https://stackoverflow.com/a/48486228/10827766
                # User: https://stackoverflow.com/users/9279401/andras-dosztal
                with Cookiejar.paths[exhentai].open() as f:
                    json.dump(cookiejar[exhentai], f, indent=4)

    def get_title(self, url):
        # Adapted From: https://www.geeksforgeeks.org/extract-title-from-a-webpage-using-python/
        def inner():
            for title in BeautifulSoup(requests.get(url).text, "html.parser").find_all(
                "title"
            ):
                return title.get_text()
            else:
                return url

        if self.sessionBuddy:
            return "Session Buddy"
        elif self.e_hentai:
            if self.__class__.e_counter < 5:
                self.__class__.e_counter += 1
            else:
                sleep(5)
                self.__class__.e_counter = 0
            if "/g/" in url:
                split_url = url.split("/g/")[1].split("/")
                gallery = dict(gid=split_url[0], token=split_url[1])
            elif "/s/" in url:
                split_url = url.split("/s/")[1].split("/")
                gallery = json.loads(
                    requests.post(
                        "https://api.e-hentai.org/api.php",
                        json=dict(
                            method="gtoken",
                            pagelist=[
                                [
                                    (gidp := split_url[1].split("-"))[0],
                                    split_url[0],
                                    gidp[1],
                                ]
                            ],
                        ),
                    ).text
                )["tokenlist"][0]
            elif "?f_search=" in url:
                return "ExHentai.org"
            else:
                return url.split("/")[-1].replace("%20", " ").replace("+", " ")
            return json.loads(
                requests.post(
                    "https://api.e-hentai.org/api.php",
                    json=dict(
                        method="gdata",
                        gidlist=[[gallery["gid"], gallery["token"]]],
                        namespace=1,
                    ),
                ).text
            )["gmetadata"][0]["title"]
        elif url.startswith("https://danbooru.donmai.us/"):
            if self.__class__.danbooru_counter < 5:
                self.__class__.danbooru_counter += 1
            else:
                sleep(5)
                self.__class__.danbooru_counter = 0
            return inner()
        else:
            try:
                return reader.title(url)
            except URLTitleError as e:
                if ("HTTP Error 404: Not Found" in str(e)) or Confirm.ask(
                    f"`urltitle' raised the following error:\n{e}\nWould you like to continue using `beautifulsoup4' instead?",
                    default=False,
                ):
                    return inner()
                else:
                    raise URLTitleError from e

    @property
    def title(self):
        return self.provided_title or self.get(
            "title",
            partial(self.get_title, self.url.replace(" ", "%20")),
        )

    def convert_to_excluded_url(self, _type):
        match _type:
            case "great":
                if self.link.startswith(excluded_urls.parse.tgs):
                    return self.link
                else:
                    prefix = excluded_urls.parse.tgs
            case "tiny":
                if self.link.startswith(excluded_urls.special.tsb):
                    return self.link
                else:
                    prefix = excluded_urls.special.tsb
        return "".join(
            (
                prefix,
                urllib.parse.quote(self.url, safe=self.safe),
                f"&title={urllib.parse.quote(self.title, safe=self.safe)}",
                f"&favIconUrl={urllib.parse.quote(self.favIconUrl, safe=self.safe)}",
                "&scroll_x=0&scroll_y=0&dark_mode=false",
            )
        )

    @property
    def json(self):
        return (
            dict(url=self.url)
            | (dict() if self.ignore_title else dict(title=self.title))
            | (dict() if self.ignore_favIconUrl else dict(favIconUrl=self.favIconUrl))
        )
