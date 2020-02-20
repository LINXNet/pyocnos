"""
Command to expose pyocnos functionality
"""
from __future__ import print_function

import argparse
import io
import logging
import sys
import textwrap

import yaml

from pyocnos import LOGGER_NAME
from pyocnos.ocnos import OCNOS


# pylint: disable=too-many-locals,too-many-arguments
def process(config_file_path, hostname, actions, save_config_file_path, candidate_file_path, verbose='0'):
    """
    Initialize device and call the actions passed in
    Args:
        config_file_path: (String) Path to the yaml file
         with username password and timeout
        hostname: (String) hostname of the device
        actions: (List) of strings e.g ['replace', 'merge', 'diff']
        save_config_file_path: (String) Where to store the running or startup config xml from device
        candidate_file_path: (String) Path to the candidate file

    Returns: (List) of Strings showing user what actions were taken

    """
    with open(config_file_path, 'r') as yml_file:
        config = yaml.safe_load(yml_file)

    username = config['config']['username']
    password = config['config']['password']
    timeout = config['config']['timeout']

    if int(verbose or '0') > 0:
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(name)s | %(levelname)s | %(filename)s/%(funcName)s:%(lineno)d | %(message)s')
        console_handler.setFormatter(formatter)
        logging.getLogger(LOGGER_NAME).setLevel(logging.DEBUG)
        logging.getLogger(LOGGER_NAME).addHandler(console_handler)

        if int(verbose) > 1:
            logging.getLogger('ncclient').setLevel(logging.DEBUG)
            logging.getLogger('ncclient').addHandler(console_handler)

    with OCNOS(hostname=hostname, username=username, password=password, timeout=timeout) as device:
        output = []
        for action in actions:
            if action == 'connection':
                output.append('Device connected: {}'.format(device.is_alive()))

            elif action in ['running', 'startup']:
                save_config_file_path = save_config_file_path or '{}-{}.xml'.format(hostname, action)
                with io.open(save_config_file_path, 'wb') as xml_file:
                    xml_file.write(device.get_config(action)[action])
                output.append('Devices {} config xml stored in {}'.format(action.capitalize(), save_config_file_path))

            else:
                device.load_candidate_config(filename=candidate_file_path)
                if action == 'diff':
                    output.append(device.compare_config())
                else:
                    device.commit_config(
                        replace_config=bool(action == 'replace')
                    )
                    output.append('Config %sd to device' % action)
        return output


def parse_and_get_args():
    """
    Create arg parser.
    Returns: argparse.ArgumentParser

    """
    parser = argparse.ArgumentParser(
        description='Diff and Replace/Merge configs.',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        'config_file_path',
        help='Config file with user details like username and password'
    )

    parser.add_argument(
        'hostname',
        help='Hostname of the switch'
    )

    parser.add_argument(
        'actions',
        nargs='+',
        choices=[
            'diff',
            'replace',
            'merge',
            'running',
            'connection',
            'startup'
        ],
        help=textwrap.dedent("""
        Please choose one or multiple actions from below
        'diff' Compare Running config with Candidate config.
        'replace' Replace Running config with Candidate config.
        'merge' Merge Candidate config with Running config.
        'running' Get running config from switch and save it to a file.
        'connection' Make a connection to device.
        'startup' Get startup config from switch and save it to a file.
        """)
    )

    parser.add_argument(
        '-s',
        '--save-config-file-path',
        dest='save_config_file_path',
        help=textwrap.dedent("""
        File path to save running or startup configs in.
        If no path is given than file will be saved in current dir
        with hostname-action.xml. For example for running config with
        hostname foo.bar foo.bar-running.xml will be created.
        """)
    )

    parser.add_argument(
        '-c',
        '--candidate-file-path',
        dest='candidate_file_path',
        help='Candidate file path',
    )

    parser.add_argument(
        '-v',
        '--verbose',
        dest='log_level',
        help=textwrap.dedent("""
        Set logging verbose level. It accepts a number >= 0.
        The default value is 0, the minimal log besides stack backtrace is given;
        Verbose level 1 enables debug level logging for pyocnos;
        Verbose level 2 emits ncclient debug level logging as well.
        """)
    )

    args = parser.parse_args()
    if any(action in args.actions for action in ['diff', 'replace', 'merge']) and not args.candidate_file_path:
        parser.error("diff, replace and merge actions requires -c, --candidate-file-path.")
    return args


def main():
    """
    Main function called from command line
    Returns: None

    """
    args = parse_and_get_args()
    output = process(
        config_file_path=args.config_file_path,
        hostname=args.hostname,
        actions=args.actions,
        save_config_file_path=args.save_config_file_path,
        candidate_file_path=args.candidate_file_path,
        verbose=args.log_level
    )
    for line in output:
        print(line)
