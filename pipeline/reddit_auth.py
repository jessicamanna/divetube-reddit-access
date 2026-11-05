"""Find linked Reddit comments that were deleted, via Reddit's official OAuth API.

Runs only with an approved Reddit app: REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env.
Without both it sends no request to Reddit at all. Not part of any default workflow: Reddit's
embeds already hide deleted comments on the site.
Usage:
    python -m pipeline.reddit_auth    # -> data/work/deleted.json (mention ids to leave out)
"""
import os
import time
from typing import Callable, Dict, List, Optional, Set

import requests

from pipeline.config import USER_AGENT, WORK
from pipeline.io import read_json, write_json

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
INFO_URL = "https://oauth.reddit.com/api/info"
OAUTH_DELAY_S = 1.0
BATCH = 100
GONE = ("[deleted]", "[removed]")


def get_app_token(client_id: str, secret: str, session) -> str:
    resp = session.post(TOKEN_URL, data={"grant_type": "client_credentials"}, auth=(client_id, secret),
                        headers={"User-Agent": USER_AGENT}, timeout=30)
    return resp.json()["access_token"]


def fetch_info(fullnames: List[str], token: str, session,
               sleep: Callable[[float], None] = time.sleep) -> Dict[str, dict]:
    """Info for each fullname, keyed by it, from the OAuth API at one request a second.

    Needs an app token: there is no unauthenticated fallback. Raises RuntimeError on any non-200,
    so a failed request never makes comments look deleted."""
    if not token:
        raise ValueError("fetch_info needs an OAuth token from an approved Reddit app")
    headers = {"User-Agent": USER_AGENT, "Authorization": f"bearer {token}"}
    out: Dict[str, dict] = {}
    for start in range(0, len(fullnames), BATCH):
        if start:
            sleep(OAUTH_DELAY_S)
        batch = fullnames[start:start + BATCH]
        resp = session.get(INFO_URL, params={"id": ",".join(batch)}, timeout=30, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Reddit info HTTP {resp.status_code}; deletion check stopped")
        for child in resp.json().get("data", {}).get("children", []):
            out[child["data"]["name"]] = child["data"]
    return out


def deleted_ids(fullnames: List[str], info: Dict[str, dict]) -> Set[str]:
    gone = set()
    for name in fullnames:
        item = info.get(name)
        if item is None or item.get("author") == "[deleted]" \
                or item.get("body") in GONE or item.get("selftext") in GONE:
            gone.add(name)
    return gone


def main(argv: Optional[List[str]] = None) -> int:
    client_id, secret = os.environ.get("REDDIT_CLIENT_ID", ""), os.environ.get("REDDIT_CLIENT_SECRET", "")
    if not (client_id and secret):
        print("Reddit API not approved/configured; deletion check skipped. No request sent to Reddit.")
        return 0
    catalog = read_json(WORK / "catalog.json")
    names = sorted({q["mention_id"] for v in catalog["videos"] for q in v["quotes"]})
    session = requests.Session()
    token = get_app_token(client_id, secret, session)
    info = fetch_info(names, token, session)
    gone = sorted(deleted_ids(names, info))
    write_json(WORK / "deleted.json", gone)
    print(f"checked {len(names)} linked comments: {len(gone)} deleted or removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
