import re


def clean_podcast_name(podcast_name: str) -> str:
    """Extract core podcast name, removing host/sponsor info.

    Removes text in parentheses/brackets, leading host info (e.g., "John Doe Presents"),
    and trailing host info (e.g., "With Brian Adams", "Hosted by...").

    Args:
        podcast_name: The official podcast name.

    Returns:
        str: The cleaned podcast name.

    Example:
        >>> clean_podcast_name("The News Today With Brian Adams")
        'The News Today'
        >>> clean_podcast_name("Brian Adams Presents The News Today")
        'The News Today'
    """
    # Remove parentheses/brackets and their contents
    cleaned = re.sub(r"\s*[\(\[].*?[\)\]]\s*", " ", podcast_name)

    # Remove leading "[Name] Presents" pattern (case-insensitive)
    cleaned = re.sub(
        r"^[a-z\s]+presents\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Remove trailing host/producer/sponsor markers with case-insensitive matching
    # Handles: "With", "Hosted By", "By", "Starring", "Featuring", "Presented By", etc.
    # Note: "by" uses lookahead to avoid matching "by" in titles like "walk by the coast"
    # The (?i:...) makes only that part case-insensitive, lookahead stays strict
    cleaned = re.sub(
        r"\s+((?i:with)|(?i:hosted\s+by)|(?i:by)\s+(?=[A-Z])|(?i:starring)|(?i:featuring)|(?i:presented\s+by)).*",
        "",
        cleaned,
    )

    # Clean up whitespace
    cleaned = " ".join(cleaned.split())
    return cleaned


def generate_acronym(podcast_name: str) -> str:
    """Generate an acronym from podcast name by taking first letter of each word.

    Args:
        podcast_name: The podcast name (typically already cleaned).

    Returns:
        str: Acronym with capitals for all words,
            e.g., "Verge of Violence" → "VOV", "The News Today" → "TNT".

    Example:
        >>> generate_acronym("Verge of Violence")
        'VOV'
        >>> generate_acronym("The News Today")
        'TNT'
        >>> generate_acronym("My Favorite Podcast")
        'MFP'
    """
    words = podcast_name.split()
    acronym = "".join(word[0].upper() for word in words if word)
    return acronym


def strip_leading_articles(name: str) -> str:
    """Remove leading articles from a string.

    Args:
        name: The string to process.

    Returns:
        str: The string with leading "The", "A", or "An" removed.

    Example:
        >>> strip_leading_articles("The 6G Podcast")
        '6G Podcast'
        >>> strip_leading_articles("A Great Show")
        'Great Show'
    """
    stripped = re.sub(r"^(the|a|an)\s+", "", name, flags=re.IGNORECASE)
    return stripped


def extract_podcast_keywords(podcast_name: str) -> list[str]:
    """Extract significant keywords from podcast name.

    Filters out common filler words to get core podcast identifiers.

    Args:
        podcast_name: The podcast name to extract keywords from.

    Returns:
        list[str]: List of significant keywords, lowercased.

    Example:
        >>> extract_podcast_keywords("SmartTechCheck Podcast and Audio Newsletter")
        ['smarttechcheck', 'podcast', 'audio', 'newsletter']
    """
    filler_words = {
        "the",
        "a",
        "an",
        "of",
        "in",
        "on",
        "at",
        "to",
        "for",
        "by",
        "and",
        "or",
        "with",
    }
    words = podcast_name.lower().split()
    return [w for w in words if w not in filler_words and w]


def build_podcast_pattern(podcast_name: str) -> str:
    """Build a regex pattern to match podcast name in various formats.

    Accounts for different variations in how podcast names appear
    at the start of episode titles (with optional colons, episode numbers, etc.).
    The pattern also captures and removes leading episode numbers.

    Args:
        podcast_name: The cleaned podcast name.

    Returns:
        str: A regex pattern (not compiled) that matches the podcast name and episode number.

    Example:
        >>> pattern = build_podcast_pattern("The News Today")
        >>> re.search(pattern, "The News Today: Breaking Story")
    """
    # Escape special regex characters
    escaped_name = re.escape(podcast_name)

    # Pattern matches from start of string:
    # - Optional "Episode X" or "Ep X" prefix with various separators
    # - Optional whitespace
    # - The podcast name (case-insensitive)
    # - Optional whitespace and colon/dash after the name
    pattern = rf"^(?:ep(?:isode)?\s*\d+[\s\-:]+)?\s*{escaped_name}\s*[-:]?\s*"

    return pattern


def remove_podcast_name(episode_title: str, podcast_name: str) -> str:
    """Remove podcast name from episode title.

    Also removes acronyms of the podcast name (e.g., "VOV" for "Verge of Violence")
    and any associated episode numbers.

    Args:
        episode_title: The full episode title.
        podcast_name: The official podcast name (will be cleaned).

    Returns:
        str: The episode title with podcast name removed, including any episode numbers.

    Example:
        >>> remove_podcast_name(
        ...     "The News Today: Breaking Climate Story",
        ...     "The News Today With Brian Adams"
        ... )
        'Breaking Climate Story'
        >>> remove_podcast_name(
        ...     "VOV 123: Hidden Truth",
        ...     "Verge of Violence"
        ... )
        'Hidden Truth'
    """
    # First, try to remove the original podcast name as-is (before cleaning)
    escaped_original = re.escape(podcast_name)
    original_pattern = rf"^(?:ep(?:isode)?\s*\d+[\s\-:]+)?\s*{escaped_original}\s*[-:]?\s*"
    result = re.sub(original_pattern, "", episode_title, flags=re.IGNORECASE).strip()

    cleaned_podcast = clean_podcast_name(podcast_name)

    # If the original name wasn't found, try the cleaned version
    if result == episode_title.strip():
        pattern = build_podcast_pattern(cleaned_podcast)
        result = re.sub(pattern, "", episode_title, flags=re.IGNORECASE).strip()

    # If still no match, try the cleaned version without leading articles
    # (e.g., "6G Podcast" instead of "The 6G Podcast")
    if result == episode_title.strip():
        stripped_podcast = strip_leading_articles(cleaned_podcast)
        if stripped_podcast != cleaned_podcast:
            pattern = build_podcast_pattern(stripped_podcast)
            result = re.sub(pattern, "", episode_title, flags=re.IGNORECASE).strip()

    # If still no match, try keyword-based matching
    # (handles cases where episode has extra words mixed in with podcast name,
    # e.g., "SmartTech Research Podcast" vs "SmartTechCheck Podcast")
    if result == episode_title.strip():
        keywords = extract_podcast_keywords(cleaned_podcast)
        if len(keywords) >= 2:  # Need at least 2 keywords to be confident
            # Use last 2 significant keywords for matching
            keyword_pattern = r"\s+".join(re.escape(kw) for kw in keywords[-2:])
            keyword_match = re.search(keyword_pattern, episode_title, re.IGNORECASE)
            if keyword_match:
                # Found keywords, remove everything up to and including the match
                result = episode_title[keyword_match.end() :].strip()
                # Clean up leading colons/dashes
                result = re.sub(r"^[\s\-:]+", "", result).strip()

    # Generate acronym and create a pattern to match it (with optional episode numbers)
    # e.g., "VOV 123:", "VoV123:", "V.O.V 42", "V.o.V", "V o V", etc.
    acronym = generate_acronym(cleaned_podcast)
    if acronym and len(acronym) > 1:  # Only if acronym has more than 1 letter
        # Pattern: acronym with optional dots/spaces between letters
        # e.g., for "VoV" matches: "VoV", "V.o.V", "V.O.V", "V o V", "V. O. V", etc.
        acronym_letters = list(acronym)
        # Insert flexible separator between letters: optional dots and/or spaces
        acronym_with_separators = r"[\.\s]*".join(acronym_letters)
        acronym_regex = rf"^{acronym_with_separators}(?:\s*[\-:])?\s*(?:\d+[\s\-:]*)?\s*"
        result = re.sub(acronym_regex, "", result, flags=re.IGNORECASE).strip()

    # If a colon remains at the start, remove it
    if result.startswith(":"):
        result = result[1:].strip()

    # If a dash remains at the start, remove it
    if result.startswith("-"):
        result = result[1:].strip()

    # Remove any remaining episode number patterns (e.g., "Episode 15 -" or "Ep 20:")
    result = re.sub(r"^(?:ep(?:isode)?\s*\d+[\s\-:]+)", "", result, flags=re.IGNORECASE).strip()

    # Remove any remaining leading colons or dashes
    result = re.sub(r"^[\s\-:]+", "", result).strip()

    return result if result else episode_title
