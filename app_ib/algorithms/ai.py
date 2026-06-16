"""
AI generation (background-only, Gemini with deterministic fallback):
  - generate_tags_for_entity()    auto-tag (cap 4) — Algorithm-adjacent (auto-tag feature)
  - generate_business_keywords()  business search keywords (cap 12)
  - generate_trend_story()        Behind-the-Trend copy (Algorithm 4)

Each function degrades gracefully: if Gemini is unconfigured/quota-limited it
returns a template/keyword fallback so the pipeline never breaks.
"""
import re

from app_ib.Utils import GeminiClient
from app_ib.Utils.EngineConfig import ALGO
from app_ib.algorithms.text import normalize

TAG_CAP = 4
KEYWORD_CAP = 12


# ---------------------------------------------------------------------------
# Auto-tags (Product / Service / Business / Shop / Architect)
# ---------------------------------------------------------------------------
def generate_tags_for_entity(title, description="", category=""):
    """Return up to 4 normalized tag strings. Gemini first, heuristic fallback."""
    prompt = (
        "You are tagging an interior-design marketplace listing. "
        "Return ONLY a JSON array of at most 4 short lowercase tags (1-2 words each), "
        "no explanations.\n"
        f"Title: {title}\nDescription: {description}\nCategory: {category}\n"
    )
    tags = GeminiClient.generate_json(prompt, temperature=0.4, max_output_tokens=128)
    out = []
    if isinstance(tags, list):
        for t in tags:
            v = normalize(str(t), strip_stopwords=True)
            if v and v not in out:
                out.append(v)
    if not out:
        out = _fallback_tags(f"{title} {category} {description}")
    return out[:TAG_CAP]


def _fallback_tags(text):
    words = [normalize(w, strip_stopwords=True) for w in re.findall(r"[A-Za-z]{4,}", text or "")]
    seen = []
    for w in words:
        if w and w not in seen:
            seen.append(w)
    return seen[:TAG_CAP]


def apply_tags(entity):
    """Generate + attach Tag rows to a Product/Service (which expose `tags` M2M)."""
    from app_ib.models import Tag
    title = getattr(entity, "title", "") or getattr(entity, "businessName", "") or getattr(entity, "name", "")
    desc = getattr(entity, "description", "") or getattr(entity, "bio", "")
    tag_values = generate_tags_for_entity(title, desc)
    tag_objs = [t for t in (Tag.getOrCreateFromText(v) for v in tag_values) if t]
    if hasattr(entity, "tags"):
        entity.tags.set(tag_objs)
    return tag_objs


# ---------------------------------------------------------------------------
# Business keywords (search recall; OR'd at normal weight)
# ---------------------------------------------------------------------------
def generate_business_keywords(business_name, category="", bio=""):
    prompt = (
        "Generate up to 12 search keywords (synonyms, use-cases, styles, budget ranges) "
        "for this interior business. Return ONLY a JSON array of lowercase strings.\n"
        f"Business: {business_name}\nCategory: {category}\nBio: {bio}\n"
    )
    kws = GeminiClient.generate_json(prompt, temperature=0.5, max_output_tokens=200)
    out = []
    if isinstance(kws, list):
        for k in kws:
            v = normalize(str(k), strip_stopwords=True)
            if v and v not in out:
                out.append(v)
    if not out:
        out = _fallback_tags(f"{business_name} {category} {bio}")
    return out[:KEYWORD_CAP]


# ---------------------------------------------------------------------------
# Behind-the-Trend story (Algorithm 4)
# ---------------------------------------------------------------------------
def generate_trend_story(business_name, rank, window_label, growth_pct):
    """Return dict with headline/eyebrow/storyTitle/storyBody/trendTags.
    Gemini (temp 0.8) first; deterministic template fallback otherwise."""
    growth_txt = f"{growth_pct:.0f}% enquiry growth" if growth_pct else "rising engagement"
    prompt = (
        "Write short editorial copy for a 'Behind the Trend' card about a trending "
        "interior-design business. Return ONLY a JSON object with keys "
        "headline, eyebrow, storyTitle, storyBody, trendTags (array of 3-5 strings).\n"
        f"Business: {business_name}\nWeekly rank: #{rank}\n"
        f"Window: {window_label}\nSignal: {growth_txt}\n"
    )
    story = GeminiClient.generate_json(prompt, temperature=ALGO.BEHIND_TREND_GEMINI_TEMPERATURE,
                                       max_output_tokens=400)
    if isinstance(story, dict) and story.get("headline") and story.get("storyBody"):
        story.setdefault("eyebrow", "Trending this week")
        story.setdefault("storyTitle", f"Why {business_name} is gaining momentum")
        tags = story.get("trendTags")
        if not isinstance(tags, list):
            story["trendTags"] = ["rising", "popular"]
        story["_source"] = "gemini"
        return story
    # deterministic fallback
    return {
        "headline": f"{business_name} is climbing the charts",
        "eyebrow": "Trending this week",
        "storyTitle": f"Why {business_name} is gaining momentum",
        "storyBody": (f"{business_name} saw strong engagement over the {window_label}, "
                      f"earning rank #{rank} on the weekly leaderboard with {growth_txt}."),
        "trendTags": ["rising", "popular"],
        "_source": "template",
    }


def generate_architect_editorial(name, city="", state="", rating=0.0):
    """Editors-pick copy for a trending architect. Gemini first, template fallback.
    Returns {eyebrow, headline, body, trendTags, source}."""
    location = ", ".join([p for p in (city, state) if p]) or "the region"
    prompt = (
        "Write a short editorial 'Editor's Pick' card for a trending interior "
        "architect on a design marketplace. Return ONLY a JSON object with keys "
        "eyebrow, headline, body, trendTags (array of 3-5 strings).\n"
        f"Architect: {name}\nLocation: {location}\nRating: {rating}\n"
    )
    copy = GeminiClient.generate_json(prompt, temperature=ALGO.BEHIND_TREND_GEMINI_TEMPERATURE,
                                      max_output_tokens=350)
    if isinstance(copy, dict) and copy.get("headline") and copy.get("body"):
        copy.setdefault("eyebrow", "Editor's Pick")
        if not isinstance(copy.get("trendTags"), list):
            copy["trendTags"] = ["design", "trending"]
        copy["source"] = "gemini"
        return copy
    return {
        "eyebrow": "Editor's Pick",
        "headline": f"{name} is shaping interiors in {location}",
        "body": (f"{name} is one of the most sought-after architects right now, "
                 f"earning a {rating}-star reputation for thoughtful, original design."),
        "trendTags": ["design", "trending", "architect"],
        "source": "template",
    }
