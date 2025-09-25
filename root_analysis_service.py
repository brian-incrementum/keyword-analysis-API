"""Utilities to run root keyword aggregation inside the FastAPI app."""
from __future__ import annotations

import collections
from typing import Dict, Iterable, List, Sequence, Tuple

from root_analysis.generate_root_analysis import (
    AUTO_STOPWORD_THRESHOLD_DEFAULT,
    DEFAULT_IRREGULAR_SINGULARS,
    DEFAULT_STOPWORDS,
    build_simple_stats,
    build_stats,
    detect_new_irregulars,
    detect_new_stopwords,
    filter_terms,
    load_config,
    preprocess_tokens,
    save_config,
)

KeywordRow = Tuple[str, int]


def _normalise_config(config: Dict[str, object]) -> Dict[str, object]:
    """Ensure config dict has the expected structure."""
    config.setdefault("stopwords", [])
    config.setdefault("irregular_singulars", {})
    auto_section = config.setdefault("auto", {})
    auto_section.setdefault("stopword_threshold", AUTO_STOPWORD_THRESHOLD_DEFAULT)
    return config


def generate_root_analysis(
    rows: Sequence[KeywordRow],
    mode: str = "full",
) -> Dict[str, object]:
    """Run the root-analysis pipeline on in-memory keyword rows.

    Args:
        rows: Sequence of (keyword, search volume) pairs.
        mode: "full" for n-gram expansion, "simple" for consolidated rows.

    Returns:
        Dictionary with the aggregated results and metadata for UI consumption.
    """
    rows_list = list(rows)

    if not rows_list:
        raise ValueError("No keyword rows supplied")

    config = _normalise_config(load_config())

    stopwords = set(DEFAULT_STOPWORDS)
    stopwords.update(config.get("stopwords", []))

    irregular_map = dict(DEFAULT_IRREGULAR_SINGULARS)
    irregular_map.update(config.get("irregular_singulars", {}))

    threshold_section = config.get("auto", {})
    threshold = float(threshold_section.get("stopword_threshold", AUTO_STOPWORD_THRESHOLD_DEFAULT))

    tokens_per_row, doc_freq, normalized_token_set, raw_token_set = preprocess_tokens(rows_list, irregular_map)

    members_map: Dict[str, List[Dict[str, int | str]]] = collections.defaultdict(list)
    for (tokens, volume), (original_keyword, _volume) in zip(tokens_per_row, rows_list):
        filtered = [token for token in tokens if token not in stopwords]
        if not filtered:
            continue
        if mode == "full":
            seen_in_term = set()
            for start in range(len(filtered)):
                for end in range(start + 1, len(filtered) + 1):
                    key = " ".join(filtered[start:end])
                    if key in seen_in_term:
                        continue
                    seen_in_term.add(key)
                    members_map[key].append({
                        "keyword": original_keyword,
                        "search_volume": volume,
                    })
        else:
            key = " ".join(filtered)
            if key:
                members_map[key].append({
                    "keyword": original_keyword,
                    "search_volume": volume,
                })

    if mode == "full":
        freq, sv_sum, first_seen = build_stats(tokens_per_row, stopwords)
        ordered_terms = filter_terms(freq, sv_sum, first_seen)
        max_sv = max((sv_sum[term] for term in ordered_terms), default=0)
        results = [
            {
                "normalized_term": term,
                "frequency": freq[term],
                "search_volume": sv_sum[term],
                "relative_volume": (sv_sum[term] / max_sv) if max_sv else 0.0,
                "members": members_map.get(term, []),
            }
            for term in ordered_terms
        ]
        root_freq = freq
    elif mode == "simple":
        ordered_terms, sv_sum, freq = build_simple_stats(tokens_per_row, stopwords)
        results = [
            {
                "normalized_term": term,
                "frequency": freq[term],
                "search_volume": sv_sum[term],
                "members": members_map.get(term, []),
            }
            for term in ordered_terms
        ]
        root_freq = freq
    else:
        raise ValueError("Mode must be 'full' or 'simple'")

    new_irregulars = detect_new_irregulars(raw_token_set, normalized_token_set, irregular_map)
    new_stopwords = detect_new_stopwords(doc_freq, len(rows_list), stopwords, threshold, root_freq)

    if new_irregulars or new_stopwords:
        if new_irregulars:
            config.setdefault("irregular_singulars", {}).update(new_irregulars)
        if new_stopwords:
            existing: Iterable[str] = config.get("stopwords", [])
            stopword_set = set(existing)
            stopword_set.update(new_stopwords)
            config["stopwords"] = sorted(stopword_set)
        save_config(config)

    return {
        "mode": mode,
        "total_keywords": len(rows_list),
        "results": results,
        "auto_config_updates": {
            "new_stopwords": sorted(new_stopwords) if new_stopwords else [],
            "new_irregular_singulars": (
                {key: new_irregulars[key] for key in sorted(new_irregulars)} if new_irregulars else {}
            ),
        },
    }
