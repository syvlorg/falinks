import json

from rich.pretty import pprint


def to_json(links, file=None):
    tabs = [link.json for link in links]
    if file:
        if file.read(1):
            file.seek(0)
            return dict(tabs=json.load(file)["tabs"] + tabs)
    return dict(tabs=tabs)


def output_file(**opts):
    if opts["sort"]:
        return "sorted_dedup" if opts["dedup"] else "sorted"
    elif opts["dedup"]:
        return "sorted_dedup" if opts["sort"] else "dedup"
    else:
        return "processed"
