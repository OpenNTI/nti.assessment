#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Weak references for assesments.

.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from functools import total_ordering

from zope import component
from zope import interface

from nti.assessment.interfaces import IQPoll
from nti.assessment.interfaces import IQuestion

from nti.ntiids.ntiids import validate_ntiid_string
from nti.ntiids.ntiids import find_object_with_ntiid

from nti.wref.interfaces import IWeakRef


@total_ordering
@interface.implementer(IWeakRef)
class ItemWeakRef(object):

    def __init__(self, item):
        self.ntiid = item.ntiid
        validate_ntiid_string(self.ntiid)

    def __eq__(self, other):
        try:
            return self is other or self.ntiid == other.ntiid
        except AttributeError:
            return NotImplemented

    def __hash__(self):
        xhash = 47
        xhash ^= hash(self.ntiid)
        return xhash

    def __lt__(self, other):
        try:
            return self.ntiid < other.ntiid
        except AttributeError:
            return NotImplemented

    def __gt__(self, other):
        try:
            return self.ntiid > other.ntiid
        except AttributeError:
            return NotImplemented

    def __getstate__(self):
        return (1, self.ntiid)

    def __setstate__(self, state):
        assert state[0] == 1
        self.ntiid = state[1]

    def __call__(self):
        return find_object_with_ntiid(self.ntiid)


@component.adapter(IQuestion)
class QuestionWeakRef(ItemWeakRef):

    def __call__(self):
        # We're not a caching weak ref
        return component.queryUtility(IQuestion, name=self.ntiid)


@component.adapter(IQPoll)
class PollWeakRef(ItemWeakRef):

    def __call__(self):
        # We're not a caching weak ref
        return component.queryUtility(IQPoll, name=self.ntiid)


def question_wref_to_missing_ntiid(ntiid):
    """
    If you have an NTIID, and the question lookup failed, but you expect
    the NTIID to appear in the future, you
    may use this function. Simply pass in a valid
    question ntiid, and a weak ref will be returned
    which you can attempt to resolve in the future.
    """

    validate_ntiid_string(ntiid)
    wref = QuestionWeakRef.__new__(QuestionWeakRef)
    wref.ntiid = ntiid
    return wref


def poll_wref_to_missing_ntiid(ntiid):
    """
    If you have an NTIID, and the poll lookup failed, but you expect
    the NTIID to appear in the future, you
    may use this function. Simply pass in a valid
    poll ntiid, and a weak ref will be returned
    which you can attempt to resolve in the future.
    """

    validate_ntiid_string(ntiid)
    wref = PollWeakRef.__new__(PollWeakRef)
    wref.ntiid = ntiid
    return wref
