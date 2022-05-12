#!/usr/bin/python3 -u

import sys
from .actions import Action
from py_console import console

def get_action_methods():
    method_list = [method for method in dir(Action) if method.startswith('__') is False]
    return method_list
    
def main():
    """
    Everything we want to wrap before we release the command
    and its child argumentes to terraform cli. If the first sys
    argument is not mapped, we release the call to terraform.
    """

    get_action_methods()
    if len(sys.argv) == 1 or not filter(sys.argv[1].startswith, get_action_methods()):
        arg = "help"
        target_environment = None
    elif "-" in sys.argv[1]:
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
        console.success("\n Execution terminated", showTime=False)
        sys.exit(130)
    except(ValueError):
        pass   
