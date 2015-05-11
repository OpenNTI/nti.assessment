#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from .interfaces import IQPartResponseNormalizer
from .interfaces import IQFreeResponsePartResponseNormalizer
from .interfaces import IQModeledContentPartResponseNormalizer
from .interfaces import IQMultipleChoicePartResponseNormalizer
from .interfaces import IQMultipleChoiceMultipleAnswerPartResponseNormalizer

@interface.implementer(IQPartResponseNormalizer)
class AbstractResponseNormalizer(object):
	
	def __init__(self, part, response):
		self.part = part
		self.response = response
	
	def __call__(self):
		raise NotImplementedError()

@interface.implementer(IQMultipleChoicePartResponseNormalizer)
class MultipleChoicePartResponseNormalizer(AbstractResponseNormalizer):
	
	def __call__(self):
		index = None
		try:
			index = self.part.choices.index( self.response.value )
		except ValueError:
			## The value they sent isn't present. Maybe they sent an
			## int string?
			try:
				index = int( self.response.value )
				## They sent an int. We can take this, if the actual value they sent
				## is not an option. If the choices are "0", "2", "3", with index 1, value "2"
				## being correct, and they send "1", we shouldn't accept that
				## TODO: Handle that case. Fortunately, it's a corner case
			except ValueError:
				## Nope, not an int. So this won't match
				index = None
		return index

@interface.implementer(IQMultipleChoiceMultipleAnswerPartResponseNormalizer)
class MultipleChoiceMultipleAnswerPartResponseNormalizer(AbstractResponseNormalizer):

	def __call__(self):
		if self.response.value:
			result = tuple(sorted(self.response.value))
		else:
			result = ()
		return result

@interface.implementer(IQFreeResponsePartResponseNormalizer)
class FreeResponsePartResponseNormalizer(AbstractResponseNormalizer):
	
	def __call__(self):
		result = self.response.value.lower() if self.response.value else u''
		return result

@interface.implementer(IQModeledContentPartResponseNormalizer)
class ModeledContentPartResponseNormalizer(AbstractResponseNormalizer):

	def __call__(self):
		result = self.response.value if self.response.value else None
		return result
