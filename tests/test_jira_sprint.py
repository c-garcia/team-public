import pytest

from datetime import datetime
from team import jira_sprint, jira_date, JIRASprint


@pytest.mark.parametrize('sprint, expected', [
    (
            'com.atlassian.greenhopper.service.sprint.Sprint@2deedb28[id=904,rapidViewId=338,state=CLOSED,name=SVP Sprint 28/9 12.12-9.1 33pt,goal=,startDate=2018-12-12T13:24:22.249Z,endDate=2019-01-08T14:24:00.000Z,completeDate=2019-01-08T16:07:53.821Z,sequence=904]',
            JIRASprint(name='SVP Sprint 28/9 12.12-9.1 33pt', start_date=jira_date('2018-12-12T13:24:22.249Z'))
    ),
    (

            'com.atlassian.greenhopper.service.sprint.Sprint@1c4be0e6[id=892,rapidViewId=338,state=CLOSED,name=SVP Sprint 27 28.11-11.12 30pt,goal=,startDate=2018-11-28T10:00:33.032Z,endDate=2018-12-12T11:00:00.000Z,completeDate=2018-12-12T09:38:43.410Z,sequence=892]',
            JIRASprint(name='SVP Sprint 27 28.11-11.12 30pt', start_date=jira_date('2018-11-28T10:00:33.032Z'))
    )
])
def test_parse_sprint(sprint, expected):
    assert jira_sprint(sprint) == expected


@pytest.mark.parametrize('invalid, why', [
    ('invalid_sprint', 'completely malformed'),
    (
            'com.atlassian.greenhopper.service.sprint.Sprint@1c4be0e6[id=892,rapidViewId=338,state=CLOSED,name=SVP Sprint 27 28.11-11.12 30pt,goal=,endDate=2018-12-12T11:00:00.000Z,completeDate=2018-12-12T09:38:43.410Z,sequence=892]',
            'missing start_date'
    )
])
def test_parse_sprint__invalid_argument(invalid, why):
    with pytest.raises(ValueError):
        jira_sprint(invalid)
