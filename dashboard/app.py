from pathlib import Path

import streamlit as st

PAGES_DIR = Path(__file__).parent / "pages"

st.set_page_config(page_title="Feed", layout="wide", initial_sidebar_state="expanded")
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"]::before {
        content: "Podex AI";
        display: block;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0.25rem 0 1rem 0;
        padding-left: 0.25rem;
        color: #e55f15;
        letter-spacing: 0.01em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_feed() -> None:
    st.header("Feed")

    episodes = [
        {
            "title": "What Changes When You Make AI a Daily Habit",
            "show": "The Practical Builder",
            "published": "Today",
            "duration": "34 min",
            "summary": (
                "A founder breaks down how small, repeatable AI workflows "
                "replaced ad-hoc busywork and freed up time for strategy."
            ),
            "tags": ["Productivity", "AI Workflows", "Founders"],
        },
        {
            "title": "Inside the Playbook of Viral Podcast Clips",
            "show": "Creator Operating System",
            "published": "Yesterday",
            "duration": "41 min",
            "summary": (
                "The episode covers scripting hooks, choosing clip moments, "
                "and turning one long-form episode into a short-form ladder."
            ),
            "tags": ["Growth", "Content", "Distribution"],
        },
        {
            "title": "From Transcript to Newsletter in Under 20 Minutes",
            "show": "The Automation Room",
            "published": "2 days ago",
            "duration": "29 min",
            "summary": (
                "A hands-on walkthrough for extracting key points from "
                "transcripts and turning them into weekly summaries."
            ),
            "tags": ["Automation", "Transcripts", "Newsletter"],
        },
        {
            "title": "Monetizing Niche Shows Without Heavy Sponsorship",
            "show": "Indie Media Tactics",
            "published": "3 days ago",
            "duration": "37 min",
            "summary": (
                "The host maps lightweight revenue options like private "
                "feeds, community tiers, and partner bundles."
            ),
            "tags": ["Monetization", "Indie Podcasts", "Audience"],
        },
    ]

    for episode in episodes:
        with st.container(border=True):
            st.subheader(episode["title"])
            st.caption(f"{episode['show']} | {episode['published']} | {episode['duration']}")
            st.write(episode["summary"])
            st.markdown(" ".join(f"`{tag}`" for tag in episode["tags"]))

        st.write("")


navigation = st.navigation(
    [
        st.Page(render_feed, title="Feed", default=True),
        st.Page(str(PAGES_DIR / "1_Library.py"), title="Library"),
        st.Page(str(PAGES_DIR / "2_AI_Search.py"), title="AI Search"),
        st.Page(str(PAGES_DIR / "3_Settings.py"), title="Settings"),
    ],
    position="sidebar",
)

navigation.run()
