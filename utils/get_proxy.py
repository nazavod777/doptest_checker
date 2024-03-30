from random import choice

from better_proxy import Proxy

with open(
        file='data/proxies.txt',
        mode='r',
        encoding='utf-8'
) as file:
    proxies_list: list = [Proxy.from_str(proxy=row.strip() if '://' in row.strip() else f'http://{row.strip()}').as_url
                          for row in file]


def get_proxy() -> str | None:
    return choice(proxies_list) if proxies_list else None
