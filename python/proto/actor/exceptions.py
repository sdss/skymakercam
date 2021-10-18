# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-12-05 12:01:21
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2017-12-05 12:19:32


from __future__ import absolute_import, division, print_function


class ProtoActorError(Exception):
    """A custom core ProtoActor exception"""

    def __init__(self, message=None):

        message = "There has been an error" if not message else message

        super(ProtoActorError, self).__init__(message)


class ProtoActorNotImplemented(ProtoActorError):
    """A custom exception for not yet implemented features."""

    def __init__(self, message=None):

        message = "This feature is not implemented yet." if not message else message

        super(ProtoActorNotImplemented, self).__init__(message)


class ProtoActorAPIError(ProtoActorError):
    """A custom exception for API errors"""

    def __init__(self, message=None):
        if not message:
            message = "Error with Http Response from ProtoActor API"
        else:
            message = "Http response error from ProtoActor API. {0}".format(message)

        super(ProtoActorAPIError, self).__init__(message)


class ProtoActorApiAuthError(ProtoActorAPIError):
    """A custom exception for API authentication errors"""

    pass


class ProtoActorMissingDependency(ProtoActorError):
    """A custom exception for missing dependencies."""

    pass


class ProtoActorWarning(Warning):
    """Base warning for ProtoActor."""


class ProtoActorUserWarning(UserWarning, ProtoActorWarning):
    """The primary warning class."""

    pass


class ProtoActorSkippedTestWarning(ProtoActorUserWarning):
    """A warning for when a test is skipped."""

    pass


class ProtoActorDeprecationWarning(ProtoActorUserWarning):
    """A warning for deprecated features."""

    pass
