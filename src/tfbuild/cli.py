#!/usr/bin/python3 -u

import sys
from .actions import Action

def main():
    """
    Everything we want to wrap before we release the command
    and its child argumentes to terraform cli. If the first sys
    argument is not mapped, we release the call to terraform.
    """
    if "-" in sys.argv[1]:
        arg = sys.argv[1].split('-')[0]
        target_environment = sys.argv[1].split('-')[1]
    else:
        arg = sys.argv[1]
        target_environment = None

    try:
        current_action = Action(arg, target_environment)
        func = getattr(current_action, arg)
        func()
    except KeyboardInterrupt:
        print("\n Execution terminated")
        sys.exit(130)
    except(ValueError):
        pass   
