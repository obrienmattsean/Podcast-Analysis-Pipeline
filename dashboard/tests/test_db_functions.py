from datetime import datetime, timedelta

import pytest
from db_functions import format_time_since_published


@pytest.mark.parametrize(
    "pub_date, expected",
    [
        (datetime.now() - timedelta(hours=5), "5 hours ago"),
        (datetime.now() - timedelta(hours=1), "1 hour ago"),
        (datetime.now() - timedelta(hours=23), "23 hours ago"),
        (datetime.now() - timedelta(hours=25), "Yesterday"),
        (datetime.now() - timedelta(hours=47), "Yesterday"),
        (datetime.now() - timedelta(days=2), "2 days ago"),
        (datetime.now() - timedelta(days=10), "10 days ago"),
    ],
)
def test_format_time_since_published(pub_date, expected):
    assert format_time_since_published(pub_date) == expected
