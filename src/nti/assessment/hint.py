#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from persistent import Persistent

from nti.assessment._util import TrivialValuedMixin

from nti.assessment.interfaces import IQHint
from nti.assessment.interfaces import IQHTMLHint
from nti.assessment.interfaces import IQTextHint


@interface.implementer(IQHint)
class QHint(Persistent):
    """
    Base class for hints.
    """


@interface.implementer(IQTextHint)
class QTextHint(TrivialValuedMixin, QHint):
    """
    A text hint.
    """


@interface.implementer(IQHTMLHint)
class QHTMLHint(TrivialValuedMixin, QHint):
    """
    A text hint.
    """
