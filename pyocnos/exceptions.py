#!/usr/bin/env python
""" Exceptions for pyocnos """

from ncclient.operations.rpc import RPCError


class OCNOSError(Exception):
    """ OcNOS Exception """
    def __init__(self, ncclient_exc=None, msg=''):
        if ncclient_exc is not None and isinstance(ncclient_exc, RPCError):
            error_msg = ('{}\n'
                         'rpc-error:\n'
                         '    error-tag: {}\n'
                         '    error-path: {}\n'
                         '    error-message: {}\n'
                         '    error-info:\n'
                         '    {}'.format(
                             msg,
                             ncclient_exc.tag or '',
                             ncclient_exc.path or '',
                             ncclient_exc.message or '',
                             ncclient_exc.info or ''
                         ))
        else:
            error_msg = msg

        super().__init__(error_msg)


class OCNOSUnOpenedConnectionError(OCNOSError):
    """
    Exception class when no connection is open
    """

    def __init__(self):
        message = 'Please open a connection first using the open().'
        super(OCNOSUnOpenedConnectionError, self).__init__(msg=message)


class OCNOSConnectionError(OCNOSError):
    """
    Exception class when couldn't open a connection
    """


class OCNOSBasicModeError(OCNOSError):
    """
    Exception class when failed to set basic mode to trim
    """


class OCNOSUnableToRetrieveConfigError(OCNOSError):
    """
       Exception class when unable to retrieve running config
    """


class OCNOSNoCandidateConfigError(OCNOSError):
    """
       Exception class when unable to load candidate config
    """

    def __init__(self):
        message = "Please provide 'filename' or 'config' attribute"
        super(OCNOSNoCandidateConfigError, self).__init__(msg=message)


class OCNOSLoadCandidateConfigFileReadError(OCNOSError):
    """
    Exception class when unable to read file give for config
    """

    def __init__(self):
        message = "Unable to read file"
        super(
            OCNOSLoadCandidateConfigFileReadError,
            self
        ).__init__(msg=message)


class OCNOSCandidateConfigNotLoadedError(OCNOSError):
    """
    Exception class when no candidate config is loaded
    """

    def __init__(self):
        message = "No candidate config loaded use load_candidate_config func"
        super(
            OCNOSCandidateConfigNotLoadedError,
            self
        ).__init__(msg=message)


class OCNOSCandidateConfigNotInServerCapabilitiesError(OCNOSError):
    """
    Exception class when no candidate config is loaded
    """

    def __init__(self):
        message = "Candidate config not in server capabilities"
        super(
            OCNOSCandidateConfigNotInServerCapabilitiesError,
            self
        ).__init__(msg=message)


class OCNOSCandidateConfigInvalidError(OCNOSError):
    """
    Exception class when candidate config is invalid
    """
