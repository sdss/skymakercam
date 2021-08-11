# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-12-05 12:01:21
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2017-12-05 12:19:32

from __future__ import print_function, division, absolute_import


class SkymakercamError(Exception):
    """A custom core Skymakercam exception"""

    def __init__(self, message=None):

        message = 'There has been an error' \
            if not message else message

        super(SkymakercamError, self).__init__(message)


class SkymakercamNotImplemented(SkymakercamError):
    """A custom exception for not yet implemented features."""

    def __init__(self, message=None):

        message = 'This feature is not implemented yet.' \
            if not message else message

        super(SkymakercamNotImplemented, self).__init__(message)


class SkymakercamAPIError(SkymakercamError):
    """A custom exception for API errors"""

    def __init__(self, message=None):
        if not message:
            message = 'Error with Http Response from Skymakercam API'
        else:
            message = 'Http response error from Skymakercam API. {0}'.format(message)

        super(SkymakercamAPIError, self).__init__(message)


class SkymakercamApiAuthError(SkymakercamAPIError):
    """A custom exception for API authentication errors"""
    pass


class SkymakercamMissingDependency(SkymakercamError):
    """A custom exception for missing dependencies."""
    pass


class SkymakercamWarning(Warning):
    """Base warning for Skymakercam."""


class SkymakercamUserWarning(UserWarning, SkymakercamWarning):
    """The primary warning class."""
    pass


class SkymakercamSkippedTestWarning(SkymakercamUserWarning):
    """A warning for when a test is skipped."""
    pass


class SkymakercamDeprecationWarning(SkymakercamUserWarning):
    """A warning for deprecated features."""
    pass
