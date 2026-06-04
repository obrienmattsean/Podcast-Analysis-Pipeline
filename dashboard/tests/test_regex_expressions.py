"""Test suite for regex_expressions module."""

import pytest
from regex_expressions import (
    build_podcast_pattern,
    clean_podcast_name,
    extract_podcast_keywords,
    generate_acronym,
    remove_podcast_name,
    strip_leading_articles,
)


class TestCleanPodcastName:
    """Tests for clean_podcast_name function."""

    def test_removes_sponsor_in_parentheses(self) -> None:
        """Should remove sponsor info in parentheses."""
        result = clean_podcast_name("The AI Podcast (Sponsored by OpenAI)")
        assert result == "The AI Podcast"

    def test_removes_sponsor_in_brackets(self) -> None:
        """Should remove sponsor info in brackets."""
        result = clean_podcast_name("The News Today [Brought to you by Company]")
        assert result == "The News Today"

    def test_removes_leading_presenter(self) -> None:
        """Should remove leading 'Person Presents' pattern."""
        result = clean_podcast_name("Brian Adams Presents The News Today")
        assert result == "The News Today"

    def test_removes_trailing_with(self) -> None:
        """Should remove trailing 'With' host info."""
        result = clean_podcast_name("The News Today With Brian Adams")
        assert result == "The News Today"

    def test_removes_trailing_hosted_by(self) -> None:
        """Should remove trailing 'Hosted By' info."""
        result = clean_podcast_name("Tech Talk Daily Hosted by Sarah Chen")
        assert result == "Tech Talk Daily"

    def test_removes_trailing_featuring(self) -> None:
        """Should remove trailing 'Featuring' info."""
        result = clean_podcast_name("My Favorite Podcast Featuring Guest Stars")
        assert result == "My Favorite Podcast"

    def test_keeps_by_in_title(self) -> None:
        """Should not remove 'by' when part of podcast title."""
        result = clean_podcast_name("Walk by the Coast")
        assert result == "Walk by the Coast"

    def test_removes_by_when_host_marker(self) -> None:
        """Should remove 'by' when followed by capitalized host name."""
        result = clean_podcast_name("Walk by the Coast by James Walker")
        assert result == "Walk by the Coast"

    def test_no_cleaning_needed(self) -> None:
        """Should return unchanged podcast name if no cleaning needed."""
        result = clean_podcast_name("The Startup Story")
        assert result == "The Startup Story"


class TestStripLeadingArticles:
    """Tests for strip_leading_articles function."""

    def test_remove_the(self) -> None:
        """Should remove leading 'The'."""
        result = strip_leading_articles("The 6G Podcast")
        assert result == "6G Podcast"

    def test_remove_a(self) -> None:
        """Should remove leading 'A'."""
        result = strip_leading_articles("A Great Show")
        assert result == "Great Show"

    def test_remove_an(self) -> None:
        """Should remove leading 'An'."""
        result = strip_leading_articles("An Amazing Podcast")
        assert result == "Amazing Podcast"

    def test_case_insensitive(self) -> None:
        """Should remove articles case-insensitively."""
        result = strip_leading_articles("the News Today")
        assert result == "News Today"

    def test_no_article_present(self) -> None:
        """Should return unchanged if no leading article."""
        result = strip_leading_articles("Podcast Name")
        assert result == "Podcast Name"


class TestExtractPodcastKeywords:
    """Tests for extract_podcast_keywords function."""

    def test_extract_significant_keywords(self) -> None:
        """Should extract significant keywords, filtering out common words."""
        result = extract_podcast_keywords("SmartTechCheck Podcast and Audio Newsletter")
        assert "smarttechcheck" in result
        assert "podcast" in result
        assert "audio" in result
        assert "newsletter" in result
        assert "and" not in result

    def test_handles_various_filler_words(self) -> None:
        """Should filter various filler words."""
        result = extract_podcast_keywords("The News Today with Brian")
        assert "news" in result
        assert "today" in result
        assert "the" not in result
        assert "with" not in result

    def test_returns_lowercase(self) -> None:
        """Should return keywords in lowercase."""
        result = extract_podcast_keywords("My Favorite Podcast")
        assert result == ["my", "favorite", "podcast"]


class TestGenerateAcronym:
    """Tests for generate_acronym function."""

    def test_three_word_acronym(self) -> None:
        """Should generate VOV from 'Verge of Violence'."""
        result = generate_acronym("Verge of Violence")
        assert result == "VOV"

    def test_two_word_acronym(self) -> None:
        """Should generate TNT from 'The News Today'."""
        result = generate_acronym("The News Today")
        assert result == "TNT"

    def test_three_word_acronym_mfp(self) -> None:
        """Should generate MFP from 'My Favorite Podcast'."""
        result = generate_acronym("My Favorite Podcast")
        assert result == "MFP"

    def test_single_word_returns_first_letter(self) -> None:
        """Should return first letter for single word."""
        result = generate_acronym("Podcast")
        assert result == "P"


class TestBuildPodcastPattern:
    """Tests for build_podcast_pattern function."""

    def test_basic_pattern_creation(self) -> None:
        """Should create pattern that matches podcast name."""
        pattern = build_podcast_pattern("The News Today")
        import re

        assert re.search(pattern, "The News Today: Breaking Story", re.IGNORECASE)

    def test_pattern_with_episode_number(self) -> None:
        """Should match episode number prefix."""
        pattern = build_podcast_pattern("The AI Podcast")
        import re

        assert re.search(pattern, "Episode 42 - The AI Podcast: Future of ML", re.IGNORECASE)

    def test_pattern_with_ep_abbreviation(self) -> None:
        """Should match 'Ep' abbreviation."""
        pattern = build_podcast_pattern("My Favorite Podcast")
        import re

        assert re.search(pattern, "Ep 15 My Favorite Podcast: Today's Topic", re.IGNORECASE)


@pytest.mark.parametrize(
    "podcast_name,episode_title,expected",
    [
        (
            "The News Today With Brian Adams",
            "The News Today: Breaking Climate Story",
            "Breaking Climate Story",
        ),
        (
            "The AI Podcast (Sponsored by OpenAI)",
            "Episode 42 - The AI Podcast: Future of ML",
            "Future of ML",
        ),
        (
            "Tech Talk Daily Hosted by Sarah Chen",
            "Tech Talk Daily - New Quantum Breakthrough",
            "New Quantum Breakthrough",
        ),
        (
            "The Startup Story",
            "Episode 1: The Startup Story - How It All Began",
            "How It All Began",
        ),
        (
            "My Favorite Podcast Featuring Guest Stars",
            "Ep 15 My Favorite Podcast: Today's Topic",
            "Today's Topic",
        ),
        (
            "Brian Adams Presents The News Today",
            "Brian Adams Presents The News Today: Breaking Climate Story",
            "Breaking Climate Story",
        ),
        (
            "Sarah Chen Presents Tech Talk Daily",
            "Episode 10 - Sarah Chen Presents Tech Talk Daily - AI Advancements",
            "AI Advancements",
        ),
        (
            "Walk by the Coast",
            "Walk by the Coast: Episode 15 - Hidden Trails",
            "Hidden Trails",
        ),
        (
            "Walk by the Coast by James Walker",
            "Walk by the Coast: Episode 15 - Hidden Trails",
            "Hidden Trails",
        ),
        (
            "Verge of Violence",
            "VOV 123: The Hidden Truth",
            "The Hidden Truth",
        ),
        (
            "Verge of Violence",
            "VoV123 - Secret Revealed",
            "Secret Revealed",
        ),
        (
            "Verge of Violence",
            "V.O.V 42: Another Episode",
            "Another Episode",
        ),
        (
            "Verge of Violence",
            "V.o.V - Mixed Case Truth",
            "Mixed Case Truth",
        ),
        (
            "Verge of Violence",
            "V o V 99: Spaced Letters",
            "Spaced Letters",
        ),
        (
            "Verge of Violence",
            "V. o. V 15: Dots and Spaces",
            "Dots and Spaces",
        ),
        (
            "The 6G Podcast by Moor Insights & Strategy",
            """6G Podcast Episode 250: Nvidia–Corning Optics Expansion, NTIA Spectrum Progress,
             5G FWA Uplink Gains, and Socorro Data Center Update""",
            """Nvidia–Corning Optics Expansion, NTIA Spectrum Progress, 5G FWA Uplink Gains,
             and Socorro Data Center Update""",
        ),
        (
            "SmartTechCheck Podcast and Audio Newsletter",
            "SmartTech Research Podcast and Audio Newsletter: Cisco Live 2026 Highlights",
            "Cisco Live 2026 Highlights",
        ),
    ],
)
def test_remove_podcast_name(podcast_name: str, episode_title: str, expected: str) -> None:
    """Test removing podcast name from various episode title formats.

    Args:
        podcast_name: The official podcast name.
        episode_title: The episode title to clean.
        expected: The expected cleaned episode title.
    """
    result = remove_podcast_name(episode_title, podcast_name)
    assert result == expected
