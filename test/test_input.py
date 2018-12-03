import unittest
import mock

from pyocnos.input import query_yes_no

raw_input_path = 'pyocnos.input.input'


class TestInput(unittest.TestCase):

    def test_query_yes_no_gives_valid_response(self):
        with mock.patch(raw_input_path) as mock_raw_input:
            answers = {
                'yes': True,
                'y': True,
                'no': False,
                'n': False
            }
            mock_raw_input.side_effect = answers.keys()
            for result in answers.values():
                self.assertEqual(query_yes_no(''), result)

    def test_query_yes_no_multiple_attempts(self):
        with mock.patch(raw_input_path) as mock_raw_input:
            answers = ['not an answer', 'i dont know', 'yes']
            mock_raw_input.side_effect = answers
            self.assertTrue(query_yes_no(''))
            self.assertEqual(mock_raw_input.call_count, len(answers))
