import dataclasses
from datetime import datetime, timezone, timedelta

import pytest

import team

issue = team.JIRAIssue(key='AAA-1', summary='sum', created=datetime.now(tz=timezone.utc), type='Story', status='Done',
                       status_category='Done')
sprint1 = team.JIRASprint(name='s1', start_date=datetime.now(tz=timezone.utc) - timedelta(days=21))
sprint2 = team.JIRASprint(name='s1', start_date=datetime.now(tz=timezone.utc) - timedelta(days=7))
qa1 = team.JIRATransition(when=datetime.now(tz=timezone.utc) - timedelta(days=21), to='QA')
done1 = team.JIRATransition(when=datetime.now(tz=timezone.utc) - timedelta(days=20), to='Done')
done2 = team.JIRATransition(when=datetime.now(tz=timezone.utc) - timedelta(days=10), to='Done')
created1 = datetime.now(tz=timezone.utc) - timedelta(days=100)


@pytest.mark.parametrize('issue, flow_time', [
    (dataclasses.replace(issue, start_sprint=sprint1, transitions=[done1]), timedelta(days=1).total_seconds()),
    (dataclasses.replace(issue, start_sprint=sprint1, transitions=[done2]), timedelta(days=11).total_seconds()),
    (dataclasses.replace(issue, start_sprint=sprint1), None)
])
def test_flow_time(issue, flow_time):
    if flow_time is not None:
        assert abs((issue.flow_time().total_seconds() - flow_time) / flow_time) < 0.01
    else:
        assert issue.flow_time() is None


@pytest.mark.parametrize('issue, flow_time', [
    (dataclasses.replace(issue, start_sprint=sprint1, transitions=[done1], created=created1),
     timedelta(days=80).total_seconds()),
    (dataclasses.replace(issue, start_sprint=sprint1), None)
])
def test_extended_flow_time(issue, flow_time):
    if flow_time is not None:
        assert abs((issue.extended_flow_time().total_seconds() - flow_time) / flow_time) < 0.01
    else:
        assert issue.extended_flow_time() is None


@pytest.mark.parametrize('issue, when', [
    (dataclasses.replace(issue, start_sprint=sprint1, transitions=[done1]), done1.when),
    (dataclasses.replace(issue), None)
])
def test_when_transitioned_to(issue, when):
    assert issue.when_transitioned_to('Done') == when


@pytest.mark.parametrize('issue, ft', [
    (dataclasses.replace(issue, labels={'FT'}), True),
    (dataclasses.replace(issue, summary='FT sum'), True),
])
def test_is_ft(issue, ft):
    assert issue.is_ft() == ft


@pytest.mark.parametrize('issue, status, time_in', [
    (dataclasses.replace(issue, transitions=[qa1, done1]), 'QA', timedelta(days=1).total_seconds()),
    (dataclasses.replace(issue, transitions=[qa1]), 'QA', timedelta(days=0).total_seconds())
])
def test_time_in(issue, status, time_in):
    diff = None
    if time_in == 0:
        diff = abs(issue.time_in('QA').total_seconds() - time_in)
    else:
        diff = abs(issue.time_in('QA').total_seconds() - time_in) / time_in
    assert diff < 0.01
