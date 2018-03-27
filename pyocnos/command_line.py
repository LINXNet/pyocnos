"""
Command to expose pyocnos functionality
"""
from __future__ import print_function
import argparse
import io
from lxml import etree
from six.moves import configparser

from pyocnos.ocnos import OCNOS


def main():
    """
    Command
    Returns: None

    """
    parser = argparse.ArgumentParser(description='Diff and apply configs.')

    parser.add_argument(
        'config',
        nargs='?',
        default='config.ini',
        help='Config file with switch and user details',
    )
    parser.add_argument(
        'candidate',
        nargs='?',
        default='candidate.xml',
        help='Candidate xml file',
    )

    parser.add_argument(
        '-d',
        '--diff',
        help='Show diff with the running config',
        action='store_true',
        dest='diff'
    )

    parser.add_argument(
        '-a',
        '--apply',
        help='Replace Running config with Candidate condig',
        action='store_true',
        dest='apply'
    )

    parser.add_argument(
        '-r',
        '--running',
        help='Get running config from switch and save it in local dir called running.xml',
        action='store_true',
        dest='running'
    )

    args = parser.parse_args()

    if not (args.diff or args.apply or args.running):
        parser.error('No action requested, add --diff or --apply or --running')

    config = configparser.ConfigParser()
    config.read(args.config)
    hostname = config.get('DEFAULT', 'hostname')
    username = config.get('DEFAULT', 'username')
    password = config.get('DEFAULT', 'password')

    with OCNOS(hostname, username, password) as device:
        if args.running:
            with io.open('running.xml', 'wb') as running_file:
                running_file.write(device.get_running_config())

        if args.diff:
            candidate_config = etree.parse(args.candidate).getroot()
            candidate_config.tag = 'config'
            candidate_config = etree.tostring(candidate_config, encoding='UTF-8')

            device.load_candidate_config(config=candidate_config)
            diff = device.compare_config()
            for line in diff:
                print(line)

        if args.apply:
            device.load_candidate_config(filename=args.candidate)
            device.commit_config()
