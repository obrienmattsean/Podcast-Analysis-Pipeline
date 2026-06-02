import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Prevent module-level Streamlit calls from failing during import of app.py.
# st.get_option must return a string so f-string interpolation doesn't break.
_st_mock = MagicMock()
_st_mock.get_option.return_value = "#ffffff"
_st_mock.navigation.return_value = MagicMock()
sys.modules.setdefault("streamlit", _st_mock)
