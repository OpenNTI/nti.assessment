#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from functools import total_ordering

from zope import interface

from nti.assessment.interfaces import QUESTION_BANK_MIME_TYPE
from nti.assessment.interfaces import RANDOMIZED_QUESTION_SET_MIME_TYPE

from nti.assessment.randomized.interfaces import IQuestionBank
from nti.assessment.randomized.interfaces import IQuestionIndexRange
from nti.assessment.randomized.interfaces import IRandomizedQuestionSet
from nti.assessment.randomized.interfaces import INonRandomizedQuestionSet
from nti.assessment.randomized.interfaces import INonRandomizedQuestionBank

from nti.assessment.question import QQuestionSet

from nti.externalization.representation import WithRepr

from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import EqHash

@interface.implementer(IRandomizedQuestionSet)
class QRandomizedQuestionSet(QQuestionSet):
	createDirectFieldProperties(IRandomizedQuestionSet)

	__external_class_name__ = "QuestionSet"
	mimeType = mime_type = RANDOMIZED_QUESTION_SET_MIME_TYPE

	nonrandomized_interface = INonRandomizedQuestionSet

@interface.implementer(IQuestionBank)
@EqHash('draw', include_super=True)
class QQuestionBank(QQuestionSet):
	createDirectFieldProperties(IQuestionBank)

	__external_class_name__ = "QuestionSet"
	mimeType = mime_type = QUESTION_BANK_MIME_TYPE

	nonrandomized_interface = INonRandomizedQuestionBank

	srand = False

	def _copy(self, result, questions=None, ranges=None, srand=None):
		result.draw = self.draw
		result.title = self.title
		result.ranges = ranges or list(self.ranges or ())
		result.questions = questions or list(self.questions or ())
		result.srand = self.srand if srand is None else bool(srand)
		return result

	def copy(self, questions=None, ranges=None, srand=None):
		result = self._copy(self.__class__(), questions, ranges, srand)
		return result

	def copyTo(self, target, questions=None, ranges=None, srand=None):
		result = self._copy(target, questions, ranges, srand)
		return result

	def summRangeDraw(self):
		if not self.ranges:
			result = self.draw
		else:
			result = sum([x.draw for x in self.ranges])
		return result

	def validate(self):
		if self.draw != self.summRangeDraw():
			raise ValueError("Sum of range draws is not equal to bank draw")
		elif self.ranges:
			# validate ranges
			sorted_ranges = sorted(self.ranges)
			for r in sorted_ranges:
				r.validate()

			# check disjoined ranges
			for idx in range(len(sorted_ranges) - 1):
				one = sorted_ranges[idx]
				two = sorted_ranges[idx + 1]
				if one.start == two.start or one.end >= two.start:
					raise ValueError("A range subsumes another")

@WithRepr
@total_ordering
@EqHash('start', 'end')
@interface.implementer(IQuestionIndexRange)
class QQuestionIndexRange(SchemaConfigured):
	createDirectFieldProperties(IQuestionIndexRange)

	draw = 1

	__external_class_name__ = "QuestionIndexRange"
	mimeType = mime_type = 'application/vnd.nextthought.naqindexrange'

	def __lt__(self, other):
		try:
			return (self.start, self.end) < (other.start, other.end)
		except AttributeError:  # pragma: no cover
			return NotImplemented

	def __gt__(self, other):
		try:
			return (self.start, self.end) > (other.start, other.end)
		except AttributeError:  # pragma: no cover
			return NotImplemented

	def validate(self):
		if self.start > self.end:
			raise ValueError("Start index cannot be greater than end index")

		if self.draw > (self.end - self.start + 1):
			raise ValueError("Invalid draw in range")

@interface.implementer(IQuestionIndexRange)
def _range_adapter(sequence):
	draw = 1 if len(sequence) < 3 else sequence[2]
	result = QQuestionIndexRange(start=int(sequence[0]),
								 end=int(sequence[1]),
								 draw=int(draw))
	return result
