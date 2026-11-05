"""The settings reddit_auth.py uses, taken from DiveTube's pipeline/config.py.

Unrelated settings are left out. No secrets live here: REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET come from the
environment (a local .env that is never committed).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "data/work"

# Diving subreddits DiveTube links to. Read-only: the app doesn't operate in any of them.
SUBREDDITS = ["scuba", "scubadiving", "cavediving", "techdiving", "ccr", "rebreathers"]
USER_AGENT = "DiveTubeBot/0.1 (+https://www.divetube.org/about)"
