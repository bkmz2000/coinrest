import json
import os
import random
from dataclasses import dataclass
import re


PROXIES = json.loads(os.environ["PROXIES"])

@dataclass
class Proxy:
    host: str
    port: int
    username: str
    password: str


class ProxyManager:

    def get_proxy(self) -> Proxy:
        proxy = random.choice(PROXIES)
        username, password, host, port = re.split('[:@]', proxy)
        return Proxy(
            username=username,
            password=password,
            host=host,
            port=int(port),
        )
