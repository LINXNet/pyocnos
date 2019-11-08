#!/usr/bin/env python
""" Exceptions for pyocnos """


class OCNOSError(Exception):
    """ OcNOS Exception """


class OCNOSUnOpenedConnectionError(OCNOSError):
    """
    Exception class when no connection is open
    """

    def __init__(self):
        message = 'Please open a connection first using the open().'
        super(OCNOSUnOpenedConnectionError, self).__init__(message)


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

    def __init__(self):
        message = 'Unable to retrieve running config.'
        super(OCNOSUnableToRetrieveConfigError, self).__init__(message)


class OCNOSNoCandidateConfigError(OCNOSError):
    """
       Exception class when unable to load candidate config
    """

    def __init__(self):
        message = "Please provide 'filename' or 'config' attribute"
        super(OCNOSNoCandidateConfigError, self).__init__(message)


class OCNOSLoadCandidateConfigFileReadError(OCNOSError):
    """
    Exception class when unable to read file give for config
    """

    def __init__(self):
        message = "Unable to read file"
        super(
            OCNOSLoadCandidateConfigFileReadError,
            self
        ).__init__(message)


class OCNOSCandidateConfigNotLoadedError(OCNOSError):
    """
    Exception class when no candidate config is loaded
    """

    def __init__(self):
        message = "No candidate config loaded use load_candidate_config func"
        super(
            OCNOSCandidateConfigNotLoadedError,
            self
        ).__init__(message)


class OCNOSCandidateConfigNotInServerCapabilitiesError(OCNOSError):
    """
    Exception class when no candidate config is loaded
    """

    def __init__(self):
        message = "Candidate config not in server capabilities"
        super(
            OCNOSCandidateConfigNotInServerCapabilitiesError,
            self
        ).__init__(message)


class OCNOSCandidateConfigInvalidError(OCNOSError):
    """
    Exception class when candidate config is invalid
    """

    def __init__(self):
        message = "Candidate config invalid."
        super(
            OCNOSCandidateConfigInvalidError,
            self
        ).__init__(message)
