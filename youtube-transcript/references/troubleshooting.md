# Troubleshooting

One branch per `error_type` in the receipt. Find the branch, act, and stop — most of these are
states, not flakiness, and retrying changes nothing.

## `IpBlocked` / `RequestBlocked`

The most common failure by far, and the one that looks least like a real error.

YouTube refuses transcript requests from IPs it does not like. Datacentre ranges — AWS, GCP, Azure,
most VPS providers — are blocked wholesale, and a residential IP can be blocked temporarily after a
burst of requests. `list()` sometimes still succeeds while `fetch()` is blocked, which makes it look
intermittent. It is not.

**Do NOT retry in a loop.** Repeated attempts deepen a temporary block.

Three remedies, cheapest first:

1. **Different network.** If the machine is on a VPN or a cloud host, run from a normal residential
   connection. This resolves it outright most of the time.
2. **Wait.** A burst-triggered block on a residential IP typically clears on its own. Come back
   later; do not sit in a retry loop.
3. **Proxy.** Configure one through the environment — never as a flag, because credentials in argv
   land in shell history and in process listings:

   ```bash
   # any HTTP(S) proxy
   export YTT_PROXY_HTTPS="http://user:pass@host:port"

   # or a Webshare residential account, which the library supports directly
   export YTT_WEBSHARE_USER="..."
   export YTT_WEBSHARE_PASS="..."
   ```

   The user sets these, not the agent. Never ask for the values in chat, never write them into a
   file, and never echo them back. A successful receipt reports `"proxy": "webshare" | "generic" |
   "none"` so the mode is visible without exposing anything.

## `ProxyError` / any `SSL*`

The proxy failed before YouTube was reached, so this says nothing about the video. Check that the
proxy is up and that `YTT_PROXY_HTTPS` / `YTT_WEBSHARE_*` are correct. If the proxy was meant to be
off, unset those variables — a stale export is the usual cause.

## `TranscriptsDisabled`

The uploader turned subtitles off. There is nothing to fetch, for any language, ever. Report it and
stop — this is not a retry candidate and no flag works around it.

## `NoTranscriptFound`

The video has transcripts, but none in the languages requested. The receipt carries an `available`
list of language codes. Retry once with a code from it:

```bash
python3 scripts/fetch_transcript.py "<target>" --languages de
```

If `available` is empty, treat it as `TranscriptsDisabled`.

To see the options without fetching anything:

```bash
python3 scripts/fetch_transcript.py "<target>" --list-only
```

## `AgeRestricted` / `PoTokenRequired`

YouTube demands an authenticated session. The library cannot supply one, and working around it means
handling the user's YouTube cookies — do not. Report that the video requires sign-in and stop.

## `VideoUnavailable` / `InvalidVideoId` / `VideoUnplayable`

Private, deleted, region-blocked, or a mistyped id. Verify the URL with the user before anything
else — a wrong id is far more likely than a broken video.

## `MissingDependency`

The plain install is in `SKILL.md` under "First run"; this branch covers only the case where it is
refused. If pip fails with `externally-managed-environment` (typical on Homebrew and system Python), do not
reach for `--break-system-packages`. Use an isolated environment instead:

```bash
uv tool install youtube-transcript-api    # if uv is available
```

or a venv beside the skill, and call that interpreter explicitly:

```bash
python3 -m venv .venv && .venv/bin/pip install youtube-transcript-api
.venv/bin/python scripts/fetch_transcript.py "<target>"
```

## `BadTarget`

The argument was not a YouTube URL or an 11-character id. Recognised shapes: `watch?v=`,
`youtu.be/`, `/embed/`, `/shorts/`, `/live/`, bare id. Playlist and channel URLs are NOT supported —
this skill fetches one video at a time. Ask the user for a specific video URL.
