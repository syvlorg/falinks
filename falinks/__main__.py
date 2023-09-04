#!/usr/bin/env python3

import rich.traceback

rich.traceback.install(show_locals=True)

from addict import Dict
from functools import wraps, partial
from importlib.resources import files
from oreo import apod
from os import sep
from rich import print
from rich.pretty import pprint
from valiant import cmapper, SuperPath

try:
    import rich_click as click
except ImportError:
    import click

from falinks.cookiejar import Cookiejar
from falinks.link import Link
from falinks.miscellaneous import output_file
from falinks.process import Process
from falinks.session_buddy import SessionBuddy
from falinks.telegram import Telegram
from falinks.variables import cookiejar

resources = files("falinks.resources")


@click.group(no_args_is_help=True)
@click.option("--dedup/--no-dedup", is_flag=True, default=True)
@click.option("-a", "--append", is_flag=True)
@click.option("-A", "--add-cookiejar", multiple=True, type=(str, click.Path()))
@click.option("-a", "--add-cookies", multiple=True, type=(str, str, str))
@click.option("-E", "--exclude", multiple=True)
@click.option("-e", "--export", is_flag=True)
@click.option("-j", "--json", is_flag=True)
@click.option("-S", "--sites", is_flag=True)
@click.option("-s", "--sort", is_flag=True)
@click.option("-U", "--use-cookiejar", multiple=True, type=(str, click.Path()))
@click.option("-u", "--use-cookies", multiple=True, type=(str, str, str))
@click.option("-v", "--verbose", count=True, default=0)
@click.pass_context
def main(
    ctx,
    add_cookiejar,
    add_cookies,
    append,
    dedup,
    exclude,
    export,
    json,
    sites,
    sort,
    use_cookiejar,
    use_cookies,
    verbose,
):
    if ctx.invoked_subcommand == "decode":
        pass
    else:
        ctx.ensure_object(dict)

        cookies = Cookiejar()
        for cookie in use_cookies:
            cookies.update({cookie[0]: {cookie[1]: cookie[2]}})
        else:
            cookiejar.update_(cookies)

        for cookie in add_cookies:
            cookiejar.update({cookie[0]: {cookie[1]: cookie[2]}})

        cookies = Cookiejar()
        for cookie in use_cookiejar:
            cookies.update({cookie[0]: cookie[1]})
        else:
            cookiejar.update_(cookies)

        for cookie in add_cookiejar:
            cookiejar.update({cookie[0]: cookie[1]})

        cookiejar.set_all()

        export_any = json or export
        if not export_any:
            verbose = verbose or 1
        ctx.obj.kwargs = dict(
            append=append,
            dedup=dedup,
            exclude=exclude,
            export_any=export_any,
            export_json=json,
            export_links=export,
            sites=sites,
            sort=sort,
            verbose=verbose,
        )


# Adapted from: https://github.com/pallets/click/issues/108#issuecomment-280489786
def params(func):
    @click.argument(
        "files",
        callback=lambda ctx, param, value: {
            SuperPath(file, strict=True) for file in value
        },
        nargs=-1,
        required=True,
    )
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@main.command(name="session-buddy")
@params
@click.pass_context
def _session_buddy(ctx, files):
    SessionBuddy(**ctx.obj.kwargs).create_and_export(*files)


@main.command(name="telegram")
@params
@click.pass_context
def _telegram(ctx, files):
    Telegram(**ctx.obj.kwargs).create_and_export(*files)


@main.command(name="process")
@params
@click.pass_context
def _process(ctx, files):
    Process(**ctx.obj.kwargs).create_and_export(*files)


@main.command()
@click.argument("links", nargs=-1, callback=cmapper(Link))
def decode(links):
    for link in links:
        print(link)


@main.command(hidden=True)
@params
@click.option(
    "-f", "--force", is_flag=True, help="Replace the test files that already exist."
)
@click.option(
    "-i",
    "--ignore-faviconurl",
    is_flag=True,
)
@click.option(
    "-I",
    "--ignore-title",
    is_flag=True,
)
@click.pass_context
def gentests(ctx, files, force, ignore_faviconurl, ignore_title):
    def Inner(output, file, ext, target, copy=False):
        output /= ext
        target = file.parent / target
        if copy:
            output.copytree(target, dirs_exist_ok=True)
            output.rmtree()
        else:
            if target.exists() and not force:
                raise FileExistsError(
                    f"Sorry; {target} already exists! Use `-f / --force' to overwrite it with {output}."
                )
            output.move(target)

    apods = tuple(apod(("dedup", "sites", "sort"), (True, False)))

    if force:
        ctx.invoke(clear_tests, files=files)

    for opts in apods:
        try:
            Process(
                export_links=True,
                export_json=True,
                ignore_favIconUrl=ignore_faviconurl,
                ignore_title=ignore_title,
                **opts,
            ).create_and_export(*(file for file in files if file.suffix == ".txt"))
            SessionBuddy(
                export_links=True,
                export_json=True,
                ignore_favIconUrl=ignore_faviconurl,
                ignore_title=ignore_title,
                **opts,
            ).create_and_export(*(file for file in files if file.suffix == ".json"))
            for file in files:
                dot_falinks = file.parent / ".falinks"
                target = output_file(**opts)
                match file.suffix:
                    case ".txt":
                        inner = partial(Inner, dot_falinks / "processed", file)
                        if opts["sites"]:
                            inner(file.stem, target)
                        else:
                            for ext in ("." + e for e in ("txt", "json")):
                                inner(file.stem + ext, target + ext)
                    case ".json":
                        Inner(
                            dot_falinks / "session_buddy",
                            file,
                            file.stem,
                            "session_buddy" + sep + target,
                            copy=True,
                        )
        finally:
            for file in files:
                if (file_falinks := file.parent / ".falinks").exists():
                    file_falinks.rmtree()


@main.command(hidden=True)
@params
@click.pass_context
def igentests(ctx, files):
    ctx.invoke(
        gentests, files=files, force=True, ignore_faviconurl=True, ignore_title=True
    )


@main.command(hidden=True)
@params
def genegs(files):
    for sites in (True, False):
        Process(
            export_links=True,
            export_json=True,
            ignore_favIconUrl=True,
            ignore_title=True,
            sites=sites,
        ).create_and_export(*(file for file in files if file.suffix == ".txt"))
        SessionBuddy(
            export_links=True,
            export_json=True,
            ignore_favIconUrl=True,
            ignore_title=True,
            sites=sites,
        ).create_and_export(*(file for file in files if file.suffix == ".json"))


@main.command(name="clear-tests", hidden=True)
@params
def clear_tests(files):
    for opts in apod(("dedup", "sites", "sort"), (True, False)):
        for file in files:
            target = file.parent / output_file(**opts)
            if target.exists():
                target.rmtree()
            for ext in ("." + e for e in ("txt", "json")):
                try:
                    target.with_suffix(ext).unlink()
                except FileNotFoundError:
                    pass


if __name__ == "__main__":
    obj = Dict()
    try:
        main(obj=obj)
    finally:
        for file in obj.cls.count_files.values():
            file.close()
