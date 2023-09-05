import difflib
import os
import requests
import subprocess
import sys

ERRORCODES = ['.github/workflows/scripts/validate_errorcodes.sh']
EVENTNAMES = ['.github/workflows/scripts/validate_events.sh']
TESTS = ['brownie', 'test','-n','8']
LINTING = ['solhint', 'contracts/**/*.sol', '|', 'grep', 'error']


def run_command(command, description, max_lines=5):
    print('#### run -> {}'.format(' '.join(command)))
    print(description)
    output = subprocess.run(command, capture_output=True, text=True)

    lines = output.stdout.split('\n')

    if len(lines) < max_lines:
        print('\n'.join(lines))
    else:
        print('\n'.join(['...'] + lines[-max_lines:]))

    return output

if '--no_unit_tests' not in sys.argv:
    run_command(TESTS, '#### run unit tests...')
else:
    print('#### NOT running unit tests')

run_command(LINTING, '#### run linting check...')
run_command(ERRORCODES, '#### run error code check...')
run_command(EVENTNAMES, '#### run event name check...')
