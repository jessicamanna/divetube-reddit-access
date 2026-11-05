# DiveTube: what touches Reddit

For Reddit's Data API reviewers. DiveTube (https://www.divetube.org) is a free, non-commercial static website listing technical diving videos that divers recommend to each other in diving subreddits. It has no ads and no accounts.

## The only code that calls Reddit's API

`pipeline/reddit_auth.py`. It does one thing: checks that the Reddit comments DiveTube links to still exist.

- **Endpoint:** read-only `GET https://oauth.reddit.com/api/info?id=<fullnames>`, up to 100 fullnames per request.
- **Which fullnames:** only the comments already linked from DiveTube's video pages (477 today, at most 3 per video).
- **Volume:** about 5 requests per run, run by hand at most once a day, paced at 1 request per second.
- **Auth:** OAuth client credentials (app-only), one `POST https://www.reddit.com/api/v1/access_token` per run. No user login, no user tokens.
- **User agent:** `DiveTubeBot/0.1 (+https://www.divetube.org/about)`.
- **Without approved credentials it does nothing.** If `REDDIT_CLIENT_ID` or `REDDIT_CLIENT_SECRET` is missing it prints a notice and exits without sending any request. There is no unauthenticated fallback.
- **Failures stop it.** Any non-200 response stops the run, so an outage never hides a comment by mistake.

It never posts, comments, votes, messages, moderates or reads private data.

## What the site does with Reddit content

- Video pages show DiveTube's own label for each linked comment (for example "Recommends"), the subreddit, the month and a "View on Reddit" link.
- The comment itself appears only through Reddit's official embed, and only after a visitor clicks "Show what this diver said". Reddit serves the text, so deleted or removed comments disappear on their own.
- DiveTube's pages and public data download contain no Reddit comment text and no usernames. A build check fails if any page contains either.
- Reddit data isn't sold, licensed, redistributed or used to train AI models.

## Files

- `pipeline/reddit_auth.py`: the API client described above.
- `pipeline/config.py`: the user agent and subreddit list. Secrets and unrelated settings are removed.
- `pipeline/io.py`: the two JSON helpers it uses.
- `tests/test_reddit_auth.py`: tests, including "no credentials means no request".

These are copied from DiveTube's private repository, unchanged apart from the trimming above. To run the tests:

```
pip install -r requirements.txt
python -m pytest -q
```

Contact: through the form at https://www.divetube.org/about/.
