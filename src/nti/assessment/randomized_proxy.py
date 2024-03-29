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
from zope.proxy import getProxiedObject

from zope.proxy.decorator import SpecificationDecoratorBase

from nti.assessment.randomized.interfaces import IQRandomizedPart

from nti.externalization.persistence import NoPickle

logger = __import__('logging').getLogger(__name__)


@NoPickle
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

    @non_overridable
    @property
    def parts(self):
        wrapped = getProxiedObject(self)
        return [RandomizedPartProxy(x) for x in wrapped.parts]

    def __getitem__(self, index):
        wrapped = getProxiedObject(self)
        return RandomizedPartProxy(wrapped.parts[index])


@NoPickle
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

    @non_overridable
    @property
    def randomized(self):
        return True

    @non_overridable
    def grade(self, *args, **kwargs):
        """
        Must go through our proxy to ensure we end up
        checking the proxy for randomized attrs in this
        call chain.

        XXX: This is fragile. We probably need to refactor the grading logic.
        """
        wrapped = getProxiedObject(self)
        grade_func = type(wrapped).grade
        return grade_func(self, *args, **kwargs)

    @non_overridable
    def _grade(self, *args, **kwargs):
        wrapped = getProxiedObject(self)
        grade_func = type(wrapped)._grade
        return grade_func(self, *args, **kwargs)
