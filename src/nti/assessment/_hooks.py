#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nti.contentfragments.interfaces import LatexContentFragment

from nti.externalization.interfaces import StandardExternalFields

CLASS = StandardExternalFields.CLASS
NTIID = StandardExternalFields.NTIID

logger = __import__('logging').getLogger(__name__)


def ntiid_object_hook(self, parsed):
    """
    In this one, rare, case, we are reading things from external
    sources and need to preserve an NTIID value.
    """
    result = False
    if NTIID in parsed and not getattr(self, 'ntiid', None):
        self.__name__ = self.ntiid = parsed[NTIID]
        result = True

    if      'value' in parsed \
        and CLASS in parsed \
        and parsed[CLASS] == 'LatexSymbolicMathSolution' \
        and parsed['value'] != self.value:
        # We started out with LatexContentFragments when we wrote these,
        # and if we re-convert when we read, we tend to over-escape
        # One thing we do need to do, though, is replace long dashes with standard
        # minus signs
        value = parsed['value'].replace(u'\u2212', u'-')
        self.value = LatexContentFragment(value)
        result = True
    return result
