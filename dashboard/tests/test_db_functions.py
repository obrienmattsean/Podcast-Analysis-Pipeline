from datetime import datetime, timedelta

import pytest
from db_functions import get_days_since_published


@pytest.mark.parametrize(
    "pub_date, expected_days",
    [
        (datetime.today() - timedelta(days=0), 0),
        (datetime.today() - timedelta(days=1), 1),
        (datetime.today() - timedelta(days=5), 5),
        (datetime.today() - timedelta(days=30), 30),
    ],
)
def test_get_days_since_published(pub_date, expected_days):
    assert get_days_since_published(pub_date) == expected_days
