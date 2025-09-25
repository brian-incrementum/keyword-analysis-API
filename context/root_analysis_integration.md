# Root Analysis Endpoint Integration Guide

## Endpoint Overview
- **Route**: `POST /root-analysis`
- **Purpose**: Run the normalized root aggregation that mirrors `root_analysis/generate_root_analysis.py` without writing temporary CSV files.
- **Authentication**: Same requirements as other API routes (none by default).

## Request Payload
Send the parsed keyword rows extracted from the uploaded CSV:

```json
{
  "mode": "full",
  "keywords": [
    { "keyword": "omega 3 gummies", "search_volume": 12000 },
    { "keyword": "omega 3 supplement", "search_volume": 8300 }
  ]
}
```

- `keywords` should include **every** row you want considered in the root roll-up (not just the preview rows) so that frequency and search-volume sums match spreadsheet output.
- `mode` accepts `full` (default) for the n-gram expansion used by the original script, or `simple` for one-to-one consolidation.

## Response Shape
Full-mode responses normalize each root phrase, count how often it appears, and provide relative weighting:

```json
{
  "mode": "full",
  "total_keywords": 6234,
  "results": [
    {
      "normalized_term": "omega 3",
      "frequency": 412,
      "search_volume": 286300,
      "relative_volume": 1.0,
      "members": [
        { "keyword": "omega 3 gummies", "search_volume": 12000 },
        { "keyword": "omega 3 supplement", "search_volume": 8300 }
      ]
    },
    {
      "normalized_term": "fish oil",
      "frequency": 177,
      "search_volume": 142050,
      "relative_volume": 0.50,
      "members": [
        { "keyword": "fish oil softgels", "search_volume": 6400 }
      ]
    }
  ],
  "auto_config_updates": {
    "new_stopwords": ["mg"],
    "new_irregular_singulars": {"children": "child"}
  }
}
```

`relative_volume` is omitted in `simple` mode, but `members` is always provided so the frontend doesn’t need to replicate normalization logic.

## Recommended Frontend Flow (Next.js)
1. **Parse the CSV once** client-side and keep the full parsed keyword array in memory until both API calls resolve.
2. Immediately after parsing, fire two parallel `fetch` calls: one to `POST /analyze-keywords` (existing flow) and one to `POST /root-analysis` with the same keyword rows.
3. Store the root-analysis response when it completes. The `members` array returned for each root already lists the contributing keywords, so no extra grouping logic is needed on the frontend. Render the UI in two stages: show the scoring results as soon as the first request finishes, then hydrate the "Root Keywords" tab once the second payload arrives.
4. Drop the large keyword array from state only after both responses have been received (or when the user aborts the run) to keep memory bounded.

This approach avoids caching on the server, minimizes perceived latency, and guarantees the root endpoint receives the full dataset even for large (6k+) CSVs.

## Error Handling Tips
- `400` responses usually indicate empty/invalid `keywords` data; surface a friendly message that the CSV may have failed to parse.
- `500` responses can mean the backend could not aggregate (e.g., malformed volumes). Log the request ID and allow the user to retry after inspecting the CSV input.
- If the backend reports new auto-learned stopwords/irregulars, consider surfacing them in developer tooling or logs to aid future debugging.
