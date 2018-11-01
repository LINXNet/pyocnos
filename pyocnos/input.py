"""
Helpers for getting cli input
"""
from distutils.util import strtobool
import sys
from future.builtins.misc import input  # pylint: disable=redefined-builtin


def query_yes_no(question):
    """
    Prompt for a yes/no question. Will keep prompting until a valid answer
    is given.
    :param question: Question for user
    :type question: str
    :return: If the user answered yes
    :rtype: bool
    """
    while True:
        try:
            choice = strtobool(input(question))
        except ValueError:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
            continue
        return bool(choice)
