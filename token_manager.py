import json
import os
import time

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

CACHE_FILE = os.path.join(os.path.dirname(__file__), ".token_cache.json")


def _fetch_token(ak_id: str, ak_secret: str, region: str) -> tuple[str, int]:
    client = AcsClient(ak_id, ak_secret, region)
    req = CommonRequest()
    req.set_domain(f"nls-meta.{region}.aliyuncs.com")
    req.set_version("2019-02-28")
    req.set_action_name("CreateToken")
    req.set_method("POST")
    resp = json.loads(client.do_action_with_exception(req))
    tk = resp["Token"]
    return tk["Id"], int(tk["ExpireTime"])


def get_token(ak_id: str, ak_secret: str, region: str = "cn-shanghai") -> str:
    now = int(time.time())
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            if (
                cache.get("ak_id") == ak_id
                and cache.get("region") == region
                and cache.get("expire", 0) - now > 600
            ):
                return cache["token"]
        except Exception:
            pass

    token, expire = _fetch_token(ak_id, ak_secret, region)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"token": token, "expire": expire, "ak_id": ak_id, "region": region}, f
        )
    return token
