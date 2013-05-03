"""
Unit tests runner for ``fhurl`` based on boundled example project (fhurl_t).
"""
import os
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = 'fhurl_t.settings'
from fhurl_t import settings

def run_tests(settings):
    from django.test.utils import get_runner

    TestRunner = get_runner(settings)
    test_runner = TestRunner(interactive=False)
    failures = test_runner.run_tests(['fhurl_t'])
    return failures

def main():
    failures = run_tests(settings)
    sys.exit(failures)

if __name__ == '__main__':
    main()

