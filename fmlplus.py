"""
fmlplus.py

Requires a fmylife API key

Created By:
    - Luke Rogers <https://github.com/lukeroge>

License:
    GPL v3
"""

import requests
import random

from lxml import etree
from urllib.parse import quote_plus

from cloudbot import hook
from cloudbot.util import colors

parser = etree.XMLParser(resolve_entities=False, no_network=True)

API_BASE = "http://api.fmylife.com/view/{}"

API_SEARCH = API_BASE.format("search")
API_RANDOM = API_BASE.format("random")
API_ID = API_BASE.format("{}/nocomment")

MULTIFML_COUNT = 3

page_store = {}


def get_random():
    params = {
        'key': api_key,
        'language': 'en'
    }
    request = requests.get(url=API_RANDOM, params=params, headers=headers)

    items = etree.fromstring(request.content, parser=parser).find('items')

    if not items:
        return None

    return items[0]


def get_by_id(query):
    params = {
        'key': api_key,
        'language': 'en'
    }
    query = quote_plus(query)
    request = requests.get(url=API_ID.format(query), params=params, headers=headers)

    items = etree.fromstring(request.content, parser=parser).find('items')

    if not items:
        return None

    return items[0]


def get_by_search(query):
    params = {
        'key': api_key,
        'search': query,
        'language': 'en'
    }
    request = requests.get(url=API_SEARCH, params=params, headers=headers)

    items = etree.fromstring(request.content, parser=parser).find('items')

    if not items:
        return None

    return random.choice(items)


def format_fml(item):
    data = {
        'id': item.get('id'),
        'category': item.find('category').text,
        'text': item.find('text').text,
        'url': item.find('short_url').text,
        '+': int(item.find('agree').text),
        '-': int(item.find('deserved').text),
        'comments': int(item.find('comments').text),
    }

    out = "(#{id}) {text}. +$(b){+}$(b)/-$(b){-}$(b)".format(**data)
    return colors.parse(out)


@hook.on_start()
def load_key(bot):
    global api_key, headers
    api_key = bot.config.get("api_keys", {}).get("fmylife", None)
    headers = {"User-Agent": bot.user_agent}


@hook.command("fmylife", "fml", autohelp=False)
def fmylife(text, message, reply):
    """ [id/search term] -- If [id], gets FML by id, if [search term], gets fml by search, else gets random FML """
    if not api_key:
        return "This command requires an API key from fmylife.com."

    if text:
        text = text.lstrip("#")
        if text.isdigit():
            item = get_by_id(text)
        else:
            item = get_by_search(text)
    else:
        item = get_random()

    if item:
        message(format_fml(item))
    else:
        reply("Not found.")


@hook.command
def multifml(text, message, reply):
    for _ in range(MULTIFML_COUNT):
        fmylife(text, message, reply)
