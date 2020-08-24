#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.proxy import ProxyBase

from nti.assessment.randomized.interfaces import IQRandomizedPart

logger = __import__('logging').getLogger(__name__)


class QuestionRandomizedPartsProxy(ProxyBase):

    __slots__ = ('question',)

    def __new__(cls, base, *unused_args, **unused_kwargs):
        return ProxyBase.__new__(cls, base)

    def __init__(self, base):
        ProxyBase.__init__(self, base)
        self.question = base

    @property
    def parts(self):
        return [RandomizedPartProxy(x) for x in self.question.parts]

    def __getitem__(self, index):
        return RandomizedPartProxy(self.question.parts[index])


@interface.implementer(IQRandomizedPart)
class RandomizedPartProxy(ProxyBase):

    __slots__ = ('part', 'randomized')
    randomized = True

    def __new__(cls, base, *unused_args, **unused_kwargs):
        return ProxyBase.__new__(cls, base)

    def __init__(self, base):
        ProxyBase.__init__(self, base)
        self.part = base
