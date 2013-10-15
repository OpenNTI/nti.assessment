#!/usr/bin/env python
"""
Implementations and support for question parts.

$Id$
"""
from __future__ import unicode_literals, print_function, absolute_import
__docformat__ = "restructuredtext en"

from zope import interface
from zope import component
from dm.zope.schema.schema import SchemaConfigured

from nti.externalization.externalization import make_repr

from . import interfaces
from .interfaces import convert_response_for_solution
from ._util import superhash

from persistent import Persistent

@interface.implementer(interfaces.IQPart)
class QPart(SchemaConfigured, Persistent):
	"""
	Base class for parts. Its :meth:`grade` method
	will attempt to transform the input based on the interfaces
	this object implements and then call the :meth:`_grade` method.
	"""


	# : The interface to which we will attempt to adapt ourself, the solution and the response
	# : when grading. Should be a :class:`.IQPartGrader`
	grader_interface = interfaces.IQPartGrader
	# : The name of the grader we will attempt to adapt to. Defaults to the default,
	# : unnamed, adapter
	grader_name = ''

	content = ''
	hints = ()
	solutions = ()
	explanation = ''

	def grade(self, response):
		for solution in self.solutions:
			# Graders return a true or false value. We are responsible
			# for applying weights to that
			result = self._grade(solution, convert_response_for_solution(solution, response))
			if result:
				return 1.0 * solution.weight
		return 0.0

	def _grade(self, solution, response):
		grader = component.getMultiAdapter((self, solution, response),
											self.grader_interface,
											name=self.grader_name)
		return grader()

	__repr__ = make_repr()

	def __eq__(self, other):
		try:
			return self is other or (self._eq_instance(other)
									 and self.content == other.content
									 and self.hints == other.hints
									 and self.solutions == other.solutions
									 and self.explanation == other.explanation
									 and self.grader_interface == other.grader_interface
									 and self.grader_name == other.grader_name)
		except AttributeError:  # pragma: no cover
			return NotImplemented

	def _eq_instance(self, other):
		return True

	def __ne__(self, other):
		return not (self == other is True)

	def __hash__(self):
		xhash = 47
		xhash ^= hash(self.content)
		xhash ^= superhash(self.hints)
		xhash ^= superhash(self.solutions)
		xhash ^= hash(self.explanation) << 5
		return xhash

@interface.implementer(interfaces.IQMathPart)
class QMathPart(QPart):

	def _eq_instance(self, other):
		return isinstance(other, QMathPart)

@interface.implementer(interfaces.IQSymbolicMathPart)
class QSymbolicMathPart(QMathPart):

	grader_interface = interfaces.IQSymbolicMathGrader

	def _eq_instance(self, other):
		return isinstance(other, QSymbolicMathPart)


@interface.implementer(interfaces.IQNumericMathPart)
class QNumericMathPart(QMathPart):

	def _eq_instance(self, other):
		return isinstance(other, QNumericMathPart)

@interface.implementer(interfaces.IQMultipleChoicePart)
class QMultipleChoicePart(QPart):

	grader_interface = interfaces.IQMultipleChoicePartGrader
	choices = ()

	def __eq__(self, other):
		try:
			return self is other or (isinstance(other, QMultipleChoicePart)
									 and super(QMultipleChoicePart, self).__eq__(other) is True
									 and self.choices == other.choices)
		except AttributeError:  # pragma: no cover
			return NotImplemented

	def __hash__(self):
		xhash = super(QMultipleChoicePart, self).__hash__()
		return xhash + superhash(self.choices)

@interface.implementer(interfaces.IQMultipleChoiceMultipleAnswerPart)
class QMultipleChoiceMultipleAnswerPart(QMultipleChoicePart):

	grader_interface = interfaces.IQMultipleChoiceMultipleAnswerPartGrader

@interface.implementer(interfaces.IQMatchingPart)
class QMatchingPart(QPart):

	grader_interface = interfaces.IQMatchingPartGrader

	labels = ()
	values = ()

	def __eq__(self, other):
		try:
			return self is other or (isinstance(other, QMatchingPart)
									 and super(QMatchingPart, self).__eq__(other) is True
									 and self.labels == other.labels
									 and self.values == other.values)
		except AttributeError:  # pragma: no cover
			return NotImplemented

	def __hash__(self):
		xhash = super(QMatchingPart, self).__hash__()
		return xhash + superhash(self.labels) + superhash(self.values)

@interface.implementer(interfaces.IQFreeResponsePart)
class QFreeResponsePart(QPart):

	grader_name = 'LowerQuoteNormalizedStringEqualityGrader'

	def _eq_instance(self, other):
		return isinstance(other, QFreeResponsePart)
