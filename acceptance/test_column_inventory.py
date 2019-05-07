import subprocess
from hamcrest import assert_that, equal_to


def test_column_inventory():
    result = subprocess.run(['python', 'columns.py', '--project', 'SVP'], stdout=subprocess.PIPE)
    assert_that(result.returncode, equal_to(0))
    assert_that()
