"""
Class to communicate with devices running OcNOS operating system
"""
import logging
# todo: Remove this once Ipinfusion have fix issue on as5812 switches for timeout
from time import sleep
import os
from binascii import hexlify

import lxml
from future.utils import raise_from
from ncclient import NCClientError
from ncclient import manager
import paramiko

from pyocnos.diff import build_xml_diff
from pyocnos.input import query_yes_no
from pyocnos.exceptions import OCNOSCandidateConfigInvalidError
from pyocnos.exceptions import OCNOSCandidateConfigNotInServerCapabilitiesError
from pyocnos.exceptions import OCNOSCandidateConfigNotLoadedError
from pyocnos.exceptions import OCNOSConnectionError
from pyocnos.exceptions import OCNOSLoadCandidateConfigFileReadError
from pyocnos.exceptions import OCNOSNoCandidateConfigError
from pyocnos.exceptions import OCNOSUnOpenedConnectionError
from pyocnos.exceptions import OCNOSUnableToRetrieveConfigError


class PromptPolicy(paramiko.MissingHostKeyPolicy):
    # pylint: disable=too-few-public-methods
    """
    Policy for prompting the user to add the host to known hosts.

    Snippets taken from paramiko.AutoAddPolicy, paramiko.RejectPolicy
    """
    def missing_host_key(self, client, hostname, key):
        # pylint: disable=protected-access
        key_name = key.get_name()
        fingerprint = hexlify(key.get_fingerprint())

        accept = query_yes_no('Unknown fingerprint of host %s.\n'
                              'The %s fingerprint is %s.\n'
                              'Do you wish to continue with the connection?'
                              % (hostname, key_name, fingerprint))
        if not accept:
            client._log(
                logging.DEBUG,
                "Rejecting {} host key for {}: {}".format(
                    key_name, hostname, fingerprint
                ),
            )
            raise paramiko.SSHException(
                "Server {!r} not found in known_hosts".format(hostname)
            )

        client._host_keys.add(hostname, key_name, key)
        if client._host_keys_filename is not None:
            client.save_host_keys(client._host_keys_filename)
        client._log(
            logging.DEBUG,
            "Adding {} host key for {}: {}".format(
                key_name, hostname, fingerprint
            ),
        )


def get_unknown_host_cb(ocnos):
    """
    Wrapper to return real callback so as ocnos properties can be accessed

    Args:
        ocnos:      instance of OCNOS class

    Returns:        unknown_host_cb function
    """
    def unknown_host_cb(host, fingerprint):
        """
        Called when there is an unknown host fingerprint

        Args:
            host:               (str) hostname
            fingerprint:        (str) RSA key fingerprint

        Returns:                (bool) Accept the fingerprint?
        """
        with paramiko.SSHClient() as ssh_client:
            keys_path = os.path.expanduser("~/.ssh/known_hosts")
            ssh_client.load_host_keys(keys_path)
            ssh_client.set_missing_host_key_policy(PromptPolicy)
            try:
                ssh_client.connect(host, username=ocnos.username,
                                   password=ocnos.password,
                                   port=ocnos.port,
                                   look_for_keys=False)
                ssh_client.close()
            except paramiko.SSHException:
                return False
        return True
    return unknown_host_cb


class OCNOS(object):
    # pylint: disable=too-many-instance-attributes
    """ Class to instantiate a OcNOS device """

    def __init__(self, hostname, username, password, timeout=60, port=830):
        # pylint: disable=too-many-arguments
        """
        OCNOS device constructor.
        Args:
            hostname:   (str) IP or FQDN of the target device
            username:   (str) Username
            password:   (str) Password
            timeout:    (int) Timeout (default: 60 sec)
            port:       (int) Port (default: 830)
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout
        self.port = port

        self._connection = None
        self._candidate_config = None
        self.log = logging.getLogger(__name__)

    def __enter__(self):
        """
        Context manager enter open connection
        Returns: OCNOS

        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        """
        Context manager enter exit connection
        Args:
            exc_type:
            exc_val:
            exc_tb:

        Returns: None

        """
        self.close()

    def open(self):
        """
        Open a connection to an OcNOS running device using SSH.

        Returns:    None
        Raises:     OCNOSConnectionError
        """

        try:
            self._connection = manager.connect(
                host=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                look_for_keys=False,
                unknown_host_cb=get_unknown_host_cb(self)
            )
            # todo: Remove this once Ipinfusion have fix issue on as5812 switches for timeout
            sleep(2)
        except NCClientError as ncclient_exception:
            self.log.error('Error', exc_info=True)
            raise_from(
                OCNOSConnectionError('Unable to open ssh connection.'),
                ncclient_exception
            )
        else:
            self.log.info(
                "Connected to '%s' for user '%s'.",
                self.hostname,
                self.username
            )

    def close(self):
        """
        Close the SSH connection to the OcNOS running device.

        Returns: None
        Raises: OCNOSConnectionError
        """
        if self._connection:
            try:
                self._connection.close_session()
            except NCClientError as ncclient_exception:
                self.log.error('error', exc_info=True)
                raise_from(
                    OCNOSConnectionError(
                        'Unable to close ssh connection.'
                    ),
                    ncclient_exception
                )
            else:
                self.log.info(
                    "Connection closed to '%s' for user '%s'.",
                    self.hostname,
                    self.username
                )
                self._connection = None

    def is_alive(self):
        """
        Check if the SSH connection is still alive.

        Returns:    (bool) True if the SSH connection is still alive.
        """
        return self._connection.connected if self._connection else False

    def load_candidate_config(self, filename=None, config=None):
        """
        Load candidate_config from a string or file like object
        Args:
            filename:       Path to the file containing the desired
                            configuration. Default: None.
            config:         String containing the desired configuration.
                            Default: None.

        Returns:            None
        Raises:             OCNOSLoadCandidateConfigError,
                            OCNOSLoadCandidateConfigFileReadError
        """
        if filename is None and config is None:
            raise OCNOSNoCandidateConfigError
        elif filename:
            try:
                self._candidate_config = lxml.etree.parse(filename).getroot()
            except IOError as io_error:
                raise_from(OCNOSLoadCandidateConfigFileReadError, io_error)
        else:
            self._candidate_config = lxml.etree.fromstring(config)
        self._candidate_config.tag = 'config'
        self.log.info('candidate_config loaded')

    def commit_config(self, replace_config=False):
        """
        Commit the loaded candidate config

        Args:
            replace_config:     (bool) True if replacing the running config
                                with the candidate config. Merging the two
                                otherwise.

        Returns:                None
        Raises:                 OCNOSUnOpenedConnectionError
                                OCNOSCandidateConfigNotLoadedError
                                OCNOSCandidateConfigNotInServerCapabilitiesError
                                OCNOSCandidateConfigInvalidError
        """

        if self._candidate_config is None:
            self.log.error('Error: Candidate config not loaded')
            raise OCNOSCandidateConfigNotLoadedError

        if not self._connection:
            self.log.error('Error: no open connection', exc_info=True)
            raise OCNOSUnOpenedConnectionError

        if ':candidate' not in self._connection.server_capabilities:
            raise OCNOSCandidateConfigNotInServerCapabilitiesError

        # discard old candidate config
        # lock the current candidate config
        # edit it
        # commit will replace the running one with candidate

        # Select the default operation. Either replacing or merging the config
        if replace_config:
            self.log.info('Replace Running config with Candidate config')
            default_operation = 'replace'
        else:
            self.log.info('Merge Candidate config with Running config')
            default_operation = 'merge'

        self._connection.discard_changes()
        with self._connection.locked(target='candidate'):
            try:
                self._connection.edit_config(
                    target='candidate',
                    config=self._candidate_config,
                    test_option='test-then-set',
                    default_operation=default_operation
                )
                self._connection.commit()
            except NCClientError as ncclient_exception:
                self.log.error('error', exc_info=True)
                raise_from(
                    OCNOSCandidateConfigInvalidError,
                    ncclient_exception
                )
        self._connection.copy_config(source='running', target='startup')

    def compare_config(self):
        """
        Diff on the running and candidate config
        Returns:        List
        Raises:         OCNOSCandidateConfigNotLoadedError
                        OCNOSUnOpenedConnectionError

        """
        if self._candidate_config is None:
            self.log.error('Error: Candidate config not loaded')
            raise OCNOSCandidateConfigNotLoadedError

        if not self._connection:
            self.log.error('Error: no open connection', exc_info=True)
            raise OCNOSUnOpenedConnectionError

        return build_xml_diff(self._get_config_from_device('running'), lxml.etree.tostring(self._candidate_config))

    def _get_config_from_device(self, config_name):
        """
        Get config from device depending on config name
        Args:
            config_name:    (str) e.g. running or startup

        Returns:            (str) xml string representing the config
        Raises:             OCNOSUnOpenedConnectionError,
                            OCNOSUnableToRetrieveConfigError
        """
        if self._connection:
            try:
                config = self._connection.get_config(
                    source=config_name,
                    with_defaults='trim'
                ).data_xml
            except NCClientError as ncclient_exception:
                self.log.error('Error', exc_info=True)
                raise_from(
                    OCNOSUnableToRetrieveConfigError,
                    ncclient_exception
                )
            else:
                running_config = lxml.etree.fromstring(config.encode())
                running_config.tag = 'config'
                return lxml.etree.tostring(running_config, encoding='UTF-8', pretty_print=True)
        else:
            self.log.error('Error', exc_info=True)
            raise OCNOSUnOpenedConnectionError

    def get_config(self, retrieve='all'):
        """
        Get all or a specific config
        Args:
            retrieve:   (str) could be all or one of startup, running,
                        or candidate

        Returns:        (dict)

        """
        return {
            'startup': self._get_config_from_device('startup') if retrieve in ('startup', 'all') else '',
            'running': self._get_config_from_device('running') if retrieve in ('running', 'all') else '',
            'candidate': self._get_config_from_device('candidate') if retrieve in ('candidate', 'all') else ''
        }

    def discard_config(self):
        """
        Clear previously loaded candidate_config without committing it.

        Returns:    None
        """

        self._candidate_config = None
        self.log.info("candidate_config discarded")
