"""Algorithm 16 — Text Normalization. Single shared, idempotent, deterministic
normalize() used for string matching and trending-search grouping.

Per spec: lowercase + collapse whitespace for everyone. Stop-word removal is
opt-in (tags/keywords only — never for search-query logging/grouping).
English-only in v1; no accent folding.
"""

# Minimal English stop-word set (used only for tags/keywords).
STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "for", "to", "in", "on", "with",
    "at", "by", "from", "as", "is", "are", "this", "that", "your", "our",
}


def normalize(s, strip_stopwords=False):
    """Lowercase + collapse all whitespace. Optionally drop stop-words.

    normalize(s) == normalize(normalize(s))           # idempotent
    normalize("Modular Kitchen") == "modular kitchen"  # deterministic
    """
    if not s:
        return ""
    tokens = str(s).lower().split()
    if strip_stopwords:
        tokens = [t for t in tokens if t not in STOP_WORDS] or tokens
    return " ".join(tokens)
