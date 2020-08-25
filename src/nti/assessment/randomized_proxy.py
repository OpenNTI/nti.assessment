"""
Proxies to enable non-randomized question parts to act as if they
are randomized.
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.proxy import ProxyBase
from zope.proxy import non_overridable

from zope.proxy.decorator import SpecificationDecoratorBase

from nti.assessment.randomized.interfaces import IQRandomizedPart

logger = __import__('logging').getLogger(__name__)


class QuestionRandomizedPartsProxy(SpecificationDecoratorBase):
    """
    A proxy for :class:`IQuestion` objects that will return
    :class:`RandomizedPartProxy` part objects. All other attributes
    will return from the base object.
    """

    def __new__(cls, base, *unused_args, **unused_kwargs):
        return ProxyBase.__new__(cls, base)

    def __init__(self, base):
        ProxyBase.__init__(self, base)
        self.question = base

    @non_overridable
    @property
    def parts(self):
        return [RandomizedPartProxy(x) for x in self.question.parts]

    def __getitem__(self, index):
        return RandomizedPartProxy(self.question.parts[index])


@interface.implementer(IQRandomizedPart)
class RandomizedPartProxy(SpecificationDecoratorBase):
    """
    A proxy for :class:`IQPart` objects that are randomized even if the
    underlying base object is not. All other attributes will return from
    the base object.
    """

    def __new__(cls, base, *unused_args, **unused_kwargs):
        return ProxyBase.__new__(cls, base)

    def __init__(self, base):
        ProxyBase.__init__(self, base)
        self.part = base

    @non_overridable
    @property
    def randomized(self):
        return True
