from __future__ import unicode_literals

import os
import sys
from unittest import TestCase

import mock

from pyocnos.command_line import main
from pyocnos.command_line import parse_and_get_args
from pyocnos.command_line import process

current_path = os.path.dirname(os.path.realpath(__file__))
ocnos_class_path = 'pyocnos.command_line.OCNOS'


class TestParseAndGetArgsFunction(TestCase):
    """
    Command line tests
    """

    def test_fail_when_config_file_name_hostname_and_actions_missing(self):
        with mock.patch.object(sys, 'argv', ['prog']):
            self.assertRaises(SystemExit, parse_and_get_args)

    def test_fail_when_hostname_and_actions_missing(self):
        with mock.patch.object(sys, 'argv', ['prog', 'test/user-details.ini']):
            self.assertRaises(SystemExit, parse_and_get_args)

    def test_fail_when_actions_missing(self):
        with mock.patch.object(sys, 'argv', ['prog', 'test/user-details.ini', 'foo.com']):
            self.assertRaises(SystemExit, parse_and_get_args)

    def test_fail_when_actions_not_from_choices(self):
        with mock.patch.object(sys, 'argv', ['prog', 'test/user-details.ini', 'foo.com', 'apple']):
            self.assertRaises(SystemExit, parse_and_get_args)

    def test_success_when_one_actions_given(self):
        with mock.patch.object(sys, 'argv', ['prog', 'test/user-details.ini', 'foo.com', 'running']):
            args = parse_and_get_args()
        self.assertEqual('test/user-details.ini', args.config_file_path)
        self.assertEqual('foo.com', args.hostname)
        self.assertEqual(['running'], args.actions)

    def test_success_when_multiple_actions_given(self):
        with mock.patch.object(sys, 'argv', ['prog', 'test/user-details.ini', 'foo.com', 'running', 'connection']):
            args = parse_and_get_args()
        self.assertEqual('test/user-details.ini', args.config_file_path)
        self.assertEqual('foo.com', args.hostname)
        self.assertEqual(['running', 'connection'], args.actions)

    def test_success_optional_file_name_argument_save_config_file_path_with_short_option(self):
        with mock.patch.object(sys, 'argv', ['prog', 'test.ini', 'foo.com', 'running', '-s', 'running-new']):
            args = parse_and_get_args()

        self.assertEqual('running-new', args.save_config_file_path)

    def test_success_optional_file_name_argument_save_config_file_path_with_long_option(self):
        with mock.patch.object(
                sys, 'argv', ['prog', 'test.ini', 'foo.com', 'running', '--save-config-file-path', 'running-new']):
            args = parse_and_get_args()

        self.assertEqual('running-new', args.save_config_file_path)

    def test_fail_when_actions_contains_diff_and_no_candidate_file_path_given(self):
        with mock.patch.object(sys, 'argv', ['prog', 'test.ini', 'foo.com', 'diff']):
            self.assertRaises(SystemExit, parse_and_get_args)

    def test_fail_when_actions_contains_replace_and_no_candidate_file_path_given(self):
        with mock.patch.object(sys, 'argv', ['prog', 'test.ini', 'foo.com', 'replace']):
            self.assertRaises(SystemExit, parse_and_get_args)

    def test_fail_when_actions_contains_merge_and_no_candidate_file_path_given(self):
        with mock.patch.object(sys, 'argv', ['prog', 'test.ini', 'foo.com', 'merge']):
            self.assertRaises(SystemExit, parse_and_get_args)

    def test_fail_when_actions_contains_diff_and_no_candidate_file_path_given(self):
        with mock.patch.object(sys, 'argv', ['prog', 'test.ini', 'foo.com', 'diff']):
            self.assertRaises(SystemExit, parse_and_get_args)

    def test_success_when_actions_contains_replace_and_candidate_file_path_given_with_short_option(self):
        with mock.patch.object(sys, 'argv', ['prog', 'test.ini', 'foo.com', 'replace', '-c', 'can-new']):
            args = parse_and_get_args()

            self.assertEqual('can-new', args.candidate_file_path)

    def test_success_when_actions_contains_merge_and_candidate_file_path_given_with_short_option(self):
        with mock.patch.object(sys, 'argv', ['prog', 'test.ini', 'foo.com', 'merge', '-c', 'can-new']):
            args = parse_and_get_args()

            self.assertEqual('can-new', args.candidate_file_path)

    def test_success_when_actions_contains_diff_and_candidate_file_path_given_with_short_option(self):
        with mock.patch.object(sys, 'argv', ['prog', 'test.ini', 'foo.com', 'diff', '-c', 'can-new']):
            args = parse_and_get_args()

            self.assertEqual('can-new', args.candidate_file_path)

    def test_success_when_actions_contains_replace_and_candidate_file_path_given_with_long_option(self):
        arguments = ['prog', 'test.ini', 'foo.com', 'replace', '--candidate-file-path', 'can-new-file']
        with mock.patch.object(sys, 'argv', arguments):
            args = parse_and_get_args()

            self.assertEqual('can-new-file', args.candidate_file_path)

    def test_success_when_actions_contains_merge_and_candidate_file_path_given_with_long_option(self):
        arguments = ['prog', 'test.ini', 'foo.com', 'merge', '--candidate-file-path', 'can-new-file']
        with mock.patch.object(sys, 'argv', arguments):
            args = parse_and_get_args()

            self.assertEqual('can-new-file', args.candidate_file_path)

    def test_success_when_actions_contains_diff_and_candidate_file_path_given_with_long_option(self):
        arguments = ['prog', 'test.ini', 'foo.com', 'diff', '--candidate-file-path', 'can-new-file']
        with mock.patch.object(sys, 'argv', arguments):
            args = parse_and_get_args()

            self.assertEqual('can-new-file', args.candidate_file_path)


class TestProcessFunction(TestCase):

    def test_fail_when_config_does_not_exist(self):
        with self.assertRaises(IOError):
            process(
                config_file_path='foo.yml',
                hostname='foo.com',
                actions=[],
                save_config_file_path=None,
                candidate_file_path=None
            )

    @mock.patch(ocnos_class_path)
    def test_success_connection(self, mock_ocnos):
        process(
            config_file_path=os.path.join(current_path, 'user-details.yml.example'),
            hostname='foobar.com',
            actions=[],
            save_config_file_path=None,
            candidate_file_path=None
        )
        mock_ocnos.assert_called_once_with(hostname='foobar.com', username='username', password='password', timeout=30)

    @mock.patch(ocnos_class_path, autospec=True)
    def test_success_connection_action(self, mock_ocnos):
        # As the OCNOS class is used in a context manager,
        # we need to mock the response from __enter__ which
        # is returned by the context manager.
        ocnos_instance = mock_ocnos.return_value.__enter__.return_value
        process(
            config_file_path=os.path.join(current_path, 'user-details.yml.example'),
            hostname='foobar.com',
            actions=['connection'],
            save_config_file_path=None,
            candidate_file_path=None
        )
        ocnos_instance.is_alive.assert_called_once()

    @mock.patch(ocnos_class_path, autospec=True)
    def test_success_running_action(self, mock_ocnos):
        ocnos_instance = mock_ocnos.return_value.__enter__.return_value
        ocnos_instance.get_config.return_value = {'running': b'Running config'}
        file_path = os.path.join(current_path, 'running.xml')
        process(
            config_file_path=os.path.join(current_path, 'user-details.yml.example'),
            hostname='foobar.com',
            actions=['running'],
            save_config_file_path=file_path,
            candidate_file_path=None
        )
        ocnos_instance.get_config.assert_called_once_with('running')
        os.remove(file_path)

    @mock.patch(ocnos_class_path, autospec=True)
    def test_success_startup_action(self, mock_ocnos):
        ocnos_instance = mock_ocnos.return_value.__enter__.return_value
        ocnos_instance.get_config.return_value = {'startup': b'Startup config'}
        file_path = os.path.join(current_path, 'startup.xml')
        process(
            config_file_path=os.path.join(current_path, 'user-details.yml.example'),
            hostname='foobar.com',
            actions=['startup'],
            save_config_file_path=file_path,
            candidate_file_path=None
        )
        ocnos_instance.get_config.assert_called_once_with('startup')
        os.remove(file_path)

    @mock.patch(ocnos_class_path, autospec=True)
    def test_success_diff_action(self, mock_ocnos):
        ocnos_instance = mock_ocnos.return_value.__enter__.return_value
        process(
            config_file_path=os.path.join(current_path, 'user-details.yml.example'),
            hostname='foobar.com',
            actions=['diff'],
            save_config_file_path=None,
            candidate_file_path='candidate.xml'
        )
        ocnos_instance.load_candidate_config.assert_called_once_with(filename='candidate.xml')
        ocnos_instance.compare_config.assert_called_once()

    @mock.patch(ocnos_class_path, autospec=True)
    def test_success_replace_action(self, mock_ocnos):
        ocnos_instance = mock_ocnos.return_value.__enter__.return_value
        process(
            config_file_path=os.path.join(current_path, 'user-details.yml.example'),
            hostname='foobar.com',
            actions=['replace'],
            save_config_file_path=None,
            candidate_file_path='candidate.xml'
        )
        ocnos_instance.load_candidate_config.assert_called_once_with(filename='candidate.xml')
        ocnos_instance.commit_config.assert_called_once()

    @mock.patch(ocnos_class_path, autospec=True)
    def test_success_merge_action(self, mock_ocnos):
        ocnos_instance = mock_ocnos.return_value.__enter__.return_value
        process(
            config_file_path=os.path.join(current_path, 'user-details.yml.example'),
            hostname='foobar.com',
            actions=['merge'],
            save_config_file_path=None,
            candidate_file_path='candidate.xml'
        )
        ocnos_instance.load_candidate_config.assert_called_once_with(filename='candidate.xml')
        ocnos_instance.commit_config.assert_called_once()

    @mock.patch(ocnos_class_path, autospec=True)
    def test_success_when_two_actions_passed(self, mock_ocnos):
        ocnos_instance = mock_ocnos.return_value.__enter__.return_value
        process(
            config_file_path=os.path.join(current_path, 'user-details.yml.example'),
            hostname='foobar.com',
            actions=['replace', 'diff'],
            save_config_file_path=None,
            candidate_file_path='candidate.xml'
        )
        ocnos_instance.load_candidate_config.assert_has_calls(
            calls=[
                mock.call(filename='candidate.xml'),
                mock.call(filename='candidate.xml')
            ]
        )
        ocnos_instance.commit_config.assert_called_once()


class TestMainFunction(TestCase):
    @mock.patch(ocnos_class_path, autospec=True)
    def test_success(self, mock_ocnos):
        config_file = os.path.join(current_path, 'user-details.yml.example')
        with mock.patch.object(sys, 'argv', ['prog', config_file, 'foo.com', 'connection']):
            ocnos_instance = mock_ocnos.return_value.__enter__.return_value
            main()
            ocnos_instance.is_alive.assert_called_once()
