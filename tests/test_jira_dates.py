from datetime import datetime, timezone
import pytest

from team import jira_date

@pytest.mark.parametrize("string, expected", [
    ('2019-01-09T10:20:40.495+0000', datetime(2019, 1, 9, 10, 20, 40, 495000, tzinfo=timezone.utc))
])
def test_parse_date(string, expected):
    assert jira_date(string) == expected

