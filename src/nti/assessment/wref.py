#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Weak references for assesments.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from functools import total_ordering

from zope import component
from zope import interface

from nti.assessment.interfaces import IQuestion

from nti.schema.schema import EqHash

from nti.ntiids.ntiids import validate_ntiid_string

from nti.wref.interfaces import IWeakRef

@total_ordering
@EqHash('ntiid')
@component.adapter(IQuestion)
@interface.implementer(IWeakRef)
class QuestionWeakRef(object):

	__slots__ = (b'ntiid',)

	def __init__(self, question):
		self.ntiid = question.ntiid
		validate_ntiid_string(self.ntiid)

	def __call__(self):
		# We're not a caching weak ref
		result = component.queryUtility(IQuestion, name=self.ntiid)
		return result

	def __lt__(self, other):
		return self.ntiid < other.ntiid

	def __getstate__(self):
		return (1, self.ntiid)

	def __setstate__(self, state):
		assert state[0] == 1
		self.ntiid = state[1]

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
