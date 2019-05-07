import json
import operator
import os
import re
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Optional, Tuple, Any, List, Set, Mapping

from jira import JIRA, Issue


@dataclass
class JIRASprint:
    name: str
    start_date: datetime


@dataclass
class JIRATransition:
    when: datetime
    to: str


@dataclass
class JIRAIssue:
    key: str
    summary: str
    created: datetime
    type: str
    status: str
    status_category: str
    resolution: Optional[str] = None
    points: Optional[int] = None
    transitions: List[JIRATransition] = field(default_factory=list)
    start_sprint: Optional[JIRASprint] = None
    end_sprint: Optional[JIRASprint] = None
    labels: Set[str] = field(default_factory=set)

    def when_transitioned_to(self, to: str) -> Optional[datetime]:
        try:
            return [s for s in self.transitions if s.to == to][0].when
        except IndexError:
            return None

    def flow_time(self) -> Optional[timedelta]:
        if self.start_sprint and self.when_transitioned_to('Done'):
            return self.when_transitioned_to('Done') - self.start_sprint.start_date
        return None

    def extended_flow_time(self) -> Optional[timedelta]:
        if self.when_transitioned_to('Done'):
            return self.when_transitioned_to('Done') - self.created
        return None

    def is_ft(self) -> bool:
        return ('FT' in self.labels) or bool(re.search('^FT', self.summary))

    def time_in(self, status: str) -> timedelta:
        try:
            idx = next(i for (i, t) in enumerate(self.transitions) if t.to == status)
            if idx >= len(self.transitions) - 1:
                return timedelta(days=0)
            return self.transitions[idx + 1].when - self.transitions[idx].when
        except StopIteration:
            return timedelta(days=0)

    def first_status(self) -> Optional[str]:
        if len(self.transitions) > 0:
            return self.transitions[0].to
        return None

    def last_status(self) -> Optional[str]:
        if len(self.transitions) > 0:
            return self.transitions[-1].to
        return None

    def time_first_last_transitions(self) -> Optional[timedelta]:
        if len(self.transitions) > 0:
            return self.transitions[-1].when - self.transitions[0].when
        return None

    def to_json(self) -> str:
        def date2str(o: Any) -> Any:
            if isinstance(o, JIRAIssue):
                return asdict(o)
            if isinstance(o, JIRASprint):
                return asdict(o)
            if isinstance(o, JIRATransition):
                return dict(when=o.when.timestamp(), to=o.to)
            if isinstance(o, datetime):
                return int(o.timestamp())
            raise TypeError(f'Cannot serialize {o}')

        return json.dumps(self, default=date2str)


def build_jira() -> JIRA:
    url = os.environ["JIRA_URL"]
    user = os.environ["JIRA_USER"]
    password = os.environ["JIRA_PASSWORD"]
    return JIRA(url, basic_auth=(user, password))


def jira_date(s: str) -> datetime:
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f%z')


def jira_sprint(s: str) -> JIRASprint:
    names = re.search('name=([^,]+)', s)
    if not names:
        raise ValueError(f'Not a JIRA string: {s}')
    dates = re.search('startDate=([^,]+)', s)
    if not dates:
        raise ValueError(f'Not a JIRA string: {s}')
    return JIRASprint(name=names[1], start_date=jira_date(dates[1]))


def valid_transition_name(n: str) -> bool:
    return n in {'Selected for Development', 'In Dev', 'In_Progress', 'Code Review', 'In QA', 'In UAT', 'Done'}


def _transitions(issue: Issue) -> List[JIRATransition]:
    if not hasattr(issue, 'changelog'):
        raise ValueError('issue should have a Changelog attribute')

    res = []
    for history in issue.changelog.histories:
        for item in history.items:
            if item.field == 'status' and valid_transition_name(item.toString):
                res.append(JIRATransition(when=jira_date(history.created), to=item.toString))
    return sorted(res, key=operator.attrgetter('when'))


def _jira_search(j: JIRA, q: str, **kwargs) -> [Issue]:
    res = []
    start = 0
    expand = kwargs.get('expand', 0)
    while True:
        chunk = j.search_issues(q, start, expand=expand)
        if len(chunk) == 0:
            break
        res += chunk
        start += len(chunk)
    return res


def _points(i: Issue) -> Optional[int]:
    if not hasattr(i.fields, 'customfield_10004') or i.fields.customfield_10004 is None:
        return None
    else:
        return int(i.fields.customfield_10004)


def _sprints(i: Issue) -> Tuple[Optional[JIRASprint], Optional[JIRASprint]]:
    if not hasattr(i.fields, 'customfield_10007') or i.fields.customfield_10007 is None \
            or len(i.fields.customfield_10007) == 0:
        return None, None
    all_sprints = sorted([jira_sprint(s) for s in i.fields.customfield_10007], key=lambda s: s.start_date)
    return all_sprints[0], all_sprints[-1]


def _issue_to_line(i: Issue) -> JIRAIssue:
    start_sprint, end_sprint = _sprints(i)

    return JIRAIssue(
        key=i.key,
        summary=i.fields.summary,
        resolution=i.fields.resolution.name if i.fields.resolution else None,
        created=jira_date(i.fields.created),
        type=i.fields.issuetype.name,
        status=i.fields.status.name,
        status_category=i.fields.status.statusCategory.name,
        points=_points(i),
        transitions=_transitions(i),
        start_sprint=start_sprint if start_sprint else None,
        end_sprint=end_sprint if end_sprint else None,
        labels={l for l in i.fields.labels}
    )


def report_query(j: JIRA, q: str) -> [JIRAIssue]:
    return [_issue_to_line(i) for i in _jira_search(j, q, expand='changelog')]


def count_statuses(j: JIRA, q: str) -> Mapping[str, int]:
    res = dict()
    for status in [i.fields.status.name for i in _jira_search(j, q)]:
        res[status] = res.get(status, 0) + 1
    return res


def count_stars(j: JIRA, q: str) -> Mapping[str, int]:
    res = {"*": 0, "**": 0}
    one_star = re.compile(r'[^*]\*([^*]|$)')
    two_star = re.compile(r'[^*]\*\*([^*]|$)')
    for summary in [i.fields.summary for i in _jira_search(j, q)]:
        if re.search(one_star, summary):
            res['*'] += 1
            continue
        if re.search(two_star, summary):
            res['**'] += 1
            continue

    return res

# backlog = team.count_stars(j, 'project = SVP and sprint not in openSprints() and statusCategory not in (Done)')
# sprint = team.count_statuses(j, 'project = SVP and sprint in openSprints()')