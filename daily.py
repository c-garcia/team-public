from dotenv import load_dotenv
import team

COL_DONE = "DONE"
COL_IN_SIGN_OFF = "IN SIGN OFF"
COL_IN_QA = "IN QA"
COL_IN_PROGRESS = "IN PROGRESS"
COL_READY_FOR_DEV = "READY FOR DEV"
COL_TODO = "TO DO"
STATUS_COL_NAMES = [COL_TODO, COL_READY_FOR_DEV, COL_IN_PROGRESS, COL_IN_QA, COL_IN_SIGN_OFF, COL_DONE]

COL_READY_FOR_3A = "READY FOR 3A"
COL_READY_FOR_SPRINT = "READY FOR SPRINT"
BACKLOG_COL_NAMES = [COL_READY_FOR_3A, COL_READY_FOR_SPRINT]


def status_to_columns(counts):
    xlation = {
        "TO DO": COL_TODO,
        "BACKLOG": COL_TODO,
        "ANALYSIS": COL_TODO,
        "IN REVIEW": COL_TODO,
        "PO REVIEW": COL_TODO,
        "READY FOR 3 AMIGOS": COL_TODO,
        "CONCEPT DEVELOPMENT": COL_TODO,
        "READY FOR SPRINT": COL_TODO,
        "SELECTED FOR DEVELOPMENT": COL_READY_FOR_DEV,
        "DELETE ME": COL_IN_PROGRESS,
        "CODE REVIEW": COL_IN_PROGRESS,
        "IN QA": COL_IN_QA,
        "PO APPROVAL": COL_IN_SIGN_OFF,
        "LIVE": COL_DONE,
        "DONE": COL_DONE
    }
    columns = {col: 0 for col in STATUS_COL_NAMES}
    for status in counts:
        columns[xlation[status.upper()]] += counts[status]
    return columns


def backlog_to_columns(counts):
    columns = {col: 0 for col in BACKLOG_COL_NAMES}
    xlation = {
        "*": COL_READY_FOR_3A,
        "**": COL_READY_FOR_SPRINT,
    }
    for status in counts:
        columns[xlation[status.upper()]] += counts[status]
    return columns


if __name__ == '__main__':
    load_dotenv()
    j = team.build_jira()
    sprint = team.count_statuses(j, 'project = SVP and sprint in openSprints()')
    sprint_counts = status_to_columns(sprint)
    backlog = team.count_stars(j, 'project = SVP and sprint not in openSprints() and statusCategory not in (Done)')
    backlog_counts = backlog_to_columns(backlog)
    total_counts = {**sprint_counts, **backlog_counts}
    print(",".join(BACKLOG_COL_NAMES + STATUS_COL_NAMES))
    print(",".join([str(total_counts[c]) for c in BACKLOG_COL_NAMES + STATUS_COL_NAMES]))
