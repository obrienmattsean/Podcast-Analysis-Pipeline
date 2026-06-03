"""Feed page — displays recent podcast episodes from the database."""

import streamlit as st
from cards import episode_card
from db_functions import get_db_connection, get_recent_episodes

st.header("Feed")

conn = get_db_connection()
recent_episodes = get_recent_episodes(conn)
conn.close()

for episode in recent_episodes:
    episode_card(episode)
