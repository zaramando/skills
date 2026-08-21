# Troubleshooting

## `MissingDependency`

```bash
brew install yt-dlp          # macOS
pipx install yt-dlp          # elsewhere
```

## `SearchFailed`

Every query failed. The `failures` array carries yt-dlp's own last line per query.

1. **yt-dlp is out of date.** YouTube changes its player constantly and yt-dlp ships fixes to match.
   First suspect: `brew upgrade yt-dlp`.
2. **Rate limiting.** Wait rather than retrying in a loop.
3. **Network or VPN.** Verify with any other yt-dlp call before blaming the skill.

Search uses the player/metadata endpoint, which is NOT the caption endpoint. A machine where
`youtube-transcript` fails with `IpBlocked` will usually search perfectly well — those are separate
blocks and one failure does not imply the other.

## `partial_failures` present on a success

Some queries failed while others returned rows. The candidate list is real but thinner than
intended, so agreement counts are understated. Say so, and consider re-running the failed phrasing
before treating a low `found_by_count` as meaningful.

## `status: empty`

No candidate survived. Read `dropped_by_filter` FIRST: if it is large, the duration filter removed
everything and the fix is the filter, not the query. Otherwise the vocabulary is wrong — go back to
`query-craft.md`.

An empty result is never evidence that no such video exists. Report it as a failed search.
