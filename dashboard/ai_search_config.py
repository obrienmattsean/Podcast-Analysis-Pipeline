"""Configuration and constants for AI Search page."""

# Search defaults
DEFAULT_TOP_K = 15
MIN_TOP_K = 5
MAX_TOP_K = 50

DEFAULT_SIMILARITY_THRESHOLD = 0.50
MIN_SIMILARITY = 0.0
MAX_SIMILARITY = 1.0
SIMILARITY_STEP = 0.05

# Placeholder and suggestions
SEARCH_PLACEHOLDER = (
    "Which podcasts discussed sustainability in the context of consumer brands in the last 30 days?"
)

SEARCH_SUGGESTIONS = [
    "Which episodes mentioned Nike?",
    "Shows with negative sentiment this week",
    "Episodes covering programmatic advertising",
    "Podcasts safe for a family brand",
]

# CSS Styles
PAGE_CSS = """
<style>

.block-container {
    max-width: 1200px;
    padding-top: 2rem;
}

.search-header {
    text-align: center;
    margin-bottom: 2rem;
}

.summary-card {
    padding: 1rem;
}

.result-card {
    padding: 1rem;
}

</style>
"""
