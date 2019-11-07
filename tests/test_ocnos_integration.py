import logging
import os
import sys
import unittest
from unittest import skip

import lxml
import yaml

from pyocnos.ocnos import OCNOS

current_path = os.path.dirname(os.path.realpath(__file__))


@skip('Devices are being used for other tests')
class TestOCNOSIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    def setUp(self):
        with open(os.path.join(current_path, 'user-details.ini'), 'r') as yml_file:
            config = yaml.load(yml_file)

        self.hostname = config['config']['hostname']
        self.username = config['config']['username']
        self.password = config['config']['password']
        self.basic_config_path = os.path.join(current_path, 'configs', 'basic.xml')

        candidate_config = lxml.etree.parse(self.basic_config_path).getroot()
        candidate_config.tag = 'config'
        candidate_config = lxml.etree.tostring(candidate_config, encoding='UTF-8')

        with OCNOS(self.hostname, self.username, self.password) as device:
            device.load_candidate_config(config=candidate_config)
            device.commit_config()

    def test_connection(self):
        with OCNOS(self.hostname, self.username, self.password) as device:
            self.assertTrue(device.is_alive())

    def test_get_running_config(self):
        with OCNOS(self.hostname, self.username, self.password) as device:
            running_config = device.get_config('running')['running'].encode('utf-8')

        self.assertEqual(
            self._clean_xml(self.basic_config_path),
            running_config.rstrip()
        )

    def test_commit_config(self):
        edited_config_path = os.path.join(
            current_path,
            'configs',
            'edited-config.xml'
        )

        candidate_config = lxml.etree.parse(edited_config_path).getroot()
        candidate_config.tag = 'config'
        with OCNOS(self.hostname, self.username, self.password) as device:
            device.load_candidate_config(
                config=lxml.etree.tostring(candidate_config)
            )
            device.commit_config()
            running_config = device.get_config('running')['running'].encode('utf-8')
        self.assertEqual(
            self._clean_xml(edited_config_path),
            running_config.rstrip()
        )

    @staticmethod
    def _clean_xml(xml_path):
        parser = lxml.etree.XMLParser(remove_blank_text=True)
        elem = lxml.etree.parse(xml_path, parser=parser)
        return lxml.etree.tostring(
            elem,
            xml_declaration=True,
            encoding='UTF-8'
        ).replace(b'\n', b'').replace(b"'", b'"')
