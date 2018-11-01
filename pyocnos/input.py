from distutils.util import strtobool
import sys


def query_yes_no(question):
    while True:
        try:
            choice = strtobool(raw_input(question))
        except ValueError:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
            continue
        return bool(choice)
