"""
Command to expose pyocnos functionality
"""
from __future__ import print_function
import argparse
import io
import textwrap

import yaml

from pyocnos.ocnos import OCNOS


def process(config_file_path, hostname, actions, save_config_file_path, candidate_file_path):
    """
    Initialize device and call the actions passed in
    Args:
        config_file_path: (String) Path to the yaml file
         with username password and timeout
        hostname: (String) hostname of the device
        actions: (List) of strings e.g ['apply', 'diff']
        save_config_file_path: (String) Where to store the running or startup config xml from device
        candidate_file_path: (String) Path to the candidate file

    Returns: (List) of Strings showing user what actions were taken

    """
    with open(config_file_path, 'r') as yml_file:
        config = yaml.load(yml_file)

    username = config['config']['username']
    password = config['config']['password']
    timeout = config['config']['timeout']

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
                    device.commit_config()
                    output.append('Config applied to device')
        return output


def parse_and_get_args():
    """
    Create arg parser.
    Returns: argparse.ArgumentParser

    """
    parser = argparse.ArgumentParser(
        description='Diff and apply configs.',
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
        choices=['diff', 'apply', 'running', 'connection', 'startup'],
        help=textwrap.dedent("""
        Please choose one or multiple actions from below
        'diff' Compare Running config with Candidate config.
        'apply' Replace Running config with Candidate config.
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

    args = parser.parse_args()
    if ('diff' in args.actions or 'apply' in args.actions) and not args.candidate_file_path:
        parser.error("diff and apply actions requires -c, --candidate-file-path.")
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
        candidate_file_path=args.candidate_file_path
    )
    for line in output:
        print(line)
