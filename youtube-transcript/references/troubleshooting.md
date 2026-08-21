# Troubleshooting

One branch per `error_type` in the receipt. Find the branch, act, and stop — most of these are
states, not flakiness, and retrying changes nothing.

## `IpBlocked` / `RequestBlocked`

The most common failure by far, and the receipt tells you which of two very different situations
you are in. Read `caption_endpoint_only` before doing anything.

### `caption_endpoint_only: true` — the usual case

YouTube answers normally; only the **caption endpoint** refuses this IP. Everything else about the
video works from this machine, which means:

- `youtube-screenshot` will succeed on the very same video. Say so — otherwise the user reasonably
  concludes their whole setup is broken.
- The underlying HTTP status is **429 Too Many Requests**. The status code says rate limiting, but
  do NOT read that as "wait and it comes back". Measured on this codebase: three spaced attempts
  over 80 minutes (gaps of 10, 25 and 45 minutes) all returned the same block, while the player and
  stream endpoints answered normally throughout. Waiting is unproven; treat it as the cheapest thing
  to try, not as the thing that works.
- It is endpoint-level, not client-level. Switching yt-dlp `player_client` (tv, ios, android,
  web_safari, mweb) hits the same 429 — verified, all five. Do not go looking for that workaround.
- A yt-dlp subtitle fallback would NOT help either: it downloads captions from the same endpoint.

Remedies, cheapest first:

1. **Different network.** VPN off, or a different connection. Datacentre ranges are throttled
   hardest, so a residential link usually works immediately. This is the remedy with evidence
   behind it — try it FIRST, ahead of waiting.
2. **Wait, but bounded.** One or two spaced attempts, then stop. Do not run an 80-minute backoff
   like the one that produced the measurement above: it cost an hour and a half and returned
   nothing. Never a tight loop, which deepens the throttle.
3. **Proxy**, configured through the environment — never as a flag, because credentials in argv land
   in shell history and process listings:

   ```bash
   export YTT_PROXY_HTTPS="http://user:pass@host:port"
   # or a Webshare residential account, which the library supports directly
   export YTT_WEBSHARE_USER="..."
   export YTT_WEBSHARE_PASS="..."
   ```

   The user sets these, not the agent. Never ask for the values in chat, never write them to a file,
   never echo them back. A successful receipt reports `"proxy": "webshare" | "generic" | "none"`, so
   the mode is visible without exposing anything.

### `caption_endpoint_only: false` — YouTube is unreachable

Even plain metadata failed, so this is not about captions. Check the network and the VPN first. If
the network is demonstrably fine, suspect the local TLS store — see the next section, which produces
exactly this symptom.

## `CERTIFICATE_VERIFY_FAILED`, or metadata that is always empty

Not an `error_type`, which is what makes it slippery: the fetch reports `caption_endpoint_only:
false`, or a successful transcript arrives with `metadata_ok: false` and an empty title.

The python.org framework builds for macOS install without a usable CA store, so `urllib` fails on
every https call while `requests` — which carries `certifi` — keeps working. The script now uses
`certifi` for its own calls, so this should not recur; if it does, the machine has neither, and the
fix is:

```bash
/Applications/Python\ 3.x/Install\ Certificates.command   # macOS python.org builds
python3 -m pip install --user certifi
```

## `BadProxyConfig`

Only one half of a Webshare credential pair is set. Both `YTT_WEBSHARE_USER` and
`YTT_WEBSHARE_PASS` are required, or neither. Rejected before any network call, so nothing left the
machine. The user fixes their own environment — never ask for the values.

## `ProxyError` / any `SSL*` during a fetch

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
