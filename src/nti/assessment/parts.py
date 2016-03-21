#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Implementations and support for question parts.

.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.component.interfaces import ComponentLookupError

from zope.container.contained import Contained

from zope.schema.interfaces import ConstraintNotSatisfied

from persistent import Persistent

from nti.assessment.common import grader_for_solution_and_response

from nti.assessment.interfaces import IQPart
from nti.assessment.interfaces import IQFilePart
from nti.assessment.interfaces import IQMathPart
from nti.assessment.interfaces import IQMatchingPart
from nti.assessment.interfaces import IQOrderingPart
from nti.assessment.interfaces import IQConnectingPart
from nti.assessment.interfaces import IQNumericMathPart
from nti.assessment.interfaces import IQFreeResponsePart
from nti.assessment.interfaces import IQSymbolicMathPart
from nti.assessment.interfaces import IQModeledContentPart
from nti.assessment.interfaces import IQMultipleChoicePart
from nti.assessment.interfaces import IQFillInTheBlankShortAnswerPart
from nti.assessment.interfaces import IQFillInTheBlankWithWordBankPart
from nti.assessment.interfaces import IQMultipleChoiceMultipleAnswerPart

from nti.assessment.interfaces import IQNonGradablePart
from nti.assessment.interfaces import IQNonGradableFilePart
from nti.assessment.interfaces import IQNonGradableMathPart
from nti.assessment.interfaces import IQNonGradableMatchingPart
from nti.assessment.interfaces import IQNonGradableOrderingPart
from nti.assessment.interfaces import IQNonGradableConnectingPart
from nti.assessment.interfaces import IQNonGradableFreeResponsePart
from nti.assessment.interfaces import IQNonGradableModeledContentPart
from nti.assessment.interfaces import IQNonGradableMultipleChoicePart
from nti.assessment.interfaces import IQNonGradableFillInTheBlankShortAnswerPart
from nti.assessment.interfaces import IQNonGradableFillInTheBlankWithWordBankPart
from nti.assessment.interfaces import IQNonGradableMultipleChoiceMultipleAnswerPart

from nti.assessment.interfaces import IQPartGrader
from nti.assessment.interfaces import IQMatchingPartGrader
from nti.assessment.interfaces import IQOrderingPartGrader
from nti.assessment.interfaces import IQSymbolicMathGrader
from nti.assessment.interfaces import IQMultipleChoicePartGrader
from nti.assessment.interfaces import IQFillInTheBlankShortAnswerGrader
from nti.assessment.interfaces import IQFillInTheBlankWithWordBankGrader
from nti.assessment.interfaces import IQMultipleChoiceMultipleAnswerPartGrader

from nti.assessment.interfaces import IQDictResponse
from nti.assessment.interfaces import IQFileResponse
from nti.assessment.interfaces import IQListResponse
from nti.assessment.interfaces import IQTextResponse
from nti.assessment.interfaces import IQModeledContentResponse

from nti.assessment.interfaces import convert_response_for_solution

from nti.contentfragments.interfaces import UnicodeContentFragment as _u

from nti.externalization.representation import WithRepr

from nti.namedfile.file import FileConstraints

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured

@WithRepr
@interface.implementer(IQNonGradablePart)
@EqHash('content', 'hints', 'explanation',
		superhash=True,
		include_type=True)
class QNonGradablePart(SchemaConfigured, Persistent):
	"""
	Base class for parts.
	"""

	response_interface = None

	hints = ()
	content = _u('')
	explanation = _u('')

@interface.implementer(IQPart)
@EqHash('content', 'hints', 'explanation',
		'solutions', 'grader_interface', 'grader_name',
		superhash=True,
		include_type=True)
class QPart(QNonGradablePart):
	"""
	Base class for parts. Its :meth:`grade` method will attempt to
	transform the input based on the interfaces this object
	implements, plus the interfaces of the solution, and then call the
	:meth:`_grade` method.

	If response_interface is non-None, then we will always attempt to convert the
	response to this interface before attempting to grade.
	In this way parts that may not have a solution
	can always be sure that the response is at least
	of an appropriate type.
	"""

	#: The interface to which we will attempt to adapt ourself, the
	#: solution and the response when grading. Should be a
	#: class:`.IQPartGrader`. The response will have first been converted
	#: for the solution.
	grader_interface = IQPartGrader

	#: The name of the grader we will attempt to adapt to. Defaults to the default,
	#: unnamed, adapter
	grader_name = _u('')

	solutions = ()

	def grade(self, response):

		if self.response_interface is not None:
			response = self.response_interface(response)

		if not self.solutions:
			# No solutions, no opinion
			return None

		result = 0.0
		for solution in self.solutions:
			# Attempt to get a proper solution
			converted = convert_response_for_solution(solution, response)
			# Graders return a true or false value. We are responsible
			# for applying weights to that
			value = self._grade(solution, converted)
			if value:
				result = self._weight(value, solution)
				break
		return result

	def _weight(self, result, solution):
		return 1.0 * solution.weight

	def _grade(self, solution, response):
		__traceback_info__ = solution, response, self.grader_name
		grader = grader_for_solution_and_response(self, solution, response)
		if grader is None:
			objects = (self, solution, response)
			raise ComponentLookupError(objects, self.grader_interface, self.grader_name)
		return grader()

# Math

@interface.implementer(IQNonGradableMathPart)
@EqHash(include_super=True, include_type=True)
class QNonGradableMathPart(QNonGradablePart):

	def _eq_instance(self, other):
		return isinstance(other, QNonGradableMathPart)

@interface.implementer(IQMathPart)
@EqHash(include_super=True, include_type=True)
class QMathPart(QPart, QNonGradableMathPart):  # order matters

	def _eq_instance(self, other):
		return isinstance(other, QMathPart)

@interface.implementer(IQSymbolicMathPart)
@EqHash(include_super=True, include_type=True)
class QSymbolicMathPart(QMathPart):
	grader_interface = IQSymbolicMathGrader

@interface.implementer(IQNumericMathPart)
@EqHash(include_super=True,
		include_type=True)
class QNumericMathPart(QMathPart):
	pass

# Multiple Choice

@interface.implementer(IQNonGradableMultipleChoicePart)
@EqHash('choices',
		include_super=True,
		include_type=True,
		superhash=True)
class QNonGradableMultipleChoicePart(QNonGradablePart):
	choices = ()
	response_interface = IQTextResponse

@interface.implementer(IQMultipleChoicePart)
@EqHash('choices',
		include_super=True,
		include_type=True,
		superhash=True)
class QMultipleChoicePart(QPart, QNonGradableMultipleChoicePart):  # order matters
	response_interface = None
	grader_interface = IQMultipleChoicePartGrader

# Multiple Choice Multiple Answer

@interface.implementer(IQNonGradableMultipleChoiceMultipleAnswerPart)
class QNonGradableMultipleChoiceMultipleAnswerPart(QNonGradableMultipleChoicePart):
	response_interface = IQListResponse

@interface.implementer(IQMultipleChoiceMultipleAnswerPart)
class QMultipleChoiceMultipleAnswerPart(QMultipleChoicePart,
										QNonGradableMultipleChoiceMultipleAnswerPart):  # order matters
	response_interface = None
	grader_interface = IQMultipleChoiceMultipleAnswerPartGrader

# Connecting

@interface.implementer(IQNonGradableConnectingPart)
@EqHash('labels', 'values',
		include_super=True,
		superhash=True)
class QNonGradableConnectingPart(QNonGradablePart):
	labels = ()
	values = ()

@interface.implementer(IQConnectingPart)
@EqHash('labels', 'values',
		include_super=True,
		superhash=True)
class QConnectingPart(QPart, QNonGradableConnectingPart):  # order matters
	pass

# CS: Spelling mistake. There maybe objects stored with
# this invalid class name
import zope.deferredimport
zope.deferredimport.initialize()
zope.deferredimport.deprecated(
	"Import from QConnectingPart instead",
	QConenctingPart='nti.assessment.parts:QConnectingPart')

@interface.implementer(IQNonGradableMatchingPart)
class QNonGradableMatchingPart(QNonGradableConnectingPart):
	pass

@interface.implementer(IQMatchingPart)
class QMatchingPart(QConnectingPart, QNonGradableMatchingPart):
	grader_interface = IQMatchingPartGrader

@interface.implementer(IQNonGradableOrderingPart)
class QNonGradableOrderingPart(QNonGradableConnectingPart):
	pass

@interface.implementer(IQOrderingPart)
class QOrderingPart(QConnectingPart, QNonGradableOrderingPart):  # order matters
	grader_interface = IQOrderingPartGrader

# Free Response

@interface.implementer(IQNonGradableFreeResponsePart)
@EqHash(include_super=True,
		include_type=True)
class QNonGradableFreeResponsePart(QNonGradablePart):
	response_interface = IQTextResponse

@interface.implementer(IQFreeResponsePart)
@EqHash(include_super=True,
		include_type=True)
class QFreeResponsePart(QPart, QNonGradableFreeResponsePart):  # order matters
	response_interface = None
	grader_name = 'LowerQuoteNormalizedStringEqualityGrader'

# File part

@interface.implementer(IQNonGradableFilePart)
@EqHash('allowed_mime_types', 'allowed_extensions', 'max_file_size',
		include_super=True,
		superhash=True)
class QNonGradableFilePart(QNonGradablePart, FileConstraints):  # order matters

	max_file_size = None
	allowed_mime_types = ()
	allowed_extensions = ()

@interface.implementer(IQFilePart)
@EqHash('allowed_mime_types', 'allowed_extensions', 'max_file_size',
		include_super=True,
		superhash=True)
class QFilePart(QPart, QNonGradableFilePart):  # order matters

	response_interface = IQFileResponse

	def grade(self, response):
		response = self.response_interface(response)
		# We first check our own constraints for submission
		# and refuse to even grade if they are not met
		if not self.is_mime_type_allowed(response.value.contentType):
			raise ConstraintNotSatisfied(response.value.contentType, 'mimeType')
		if not self.is_filename_allowed(response.value.filename):
			raise ConstraintNotSatisfied(response.value.filename, 'filename')
		if (self.max_file_size is not None and response.value.getSize() > self.max_file_size):
			raise ConstraintNotSatisfied(response.value.getSize(), 'max_file_size')

		super(QFilePart, self).grade(response)

# Modeled Content

@interface.implementer(IQNonGradableModeledContentPart)
@EqHash(include_super=True,
		include_type=True)
class QNonGradableModeledContentPart(QNonGradablePart):
	response_interface = IQModeledContentResponse

@interface.implementer(IQModeledContentPart)
@EqHash(include_super=True,
		include_type=True)
class QModeledContentPart(QPart, QNonGradableModeledContentPart):  # order matters
	pass

# Fill in the Blank

@interface.implementer(IQNonGradableFillInTheBlankShortAnswerPart)
class QNonGradableFillInTheBlankShortAnswerPart(QNonGradablePart):
	response_interface = IQDictResponse

@interface.implementer(IQFillInTheBlankShortAnswerPart)
class QFillInTheBlankShortAnswerPart(QPart, QNonGradableFillInTheBlankShortAnswerPart):  # order matters
	grader_interface = IQFillInTheBlankShortAnswerGrader

@interface.implementer(IQNonGradableFillInTheBlankWithWordBankPart)
class QNonGradableFillInTheBlankWithWordBankPart(QNonGradablePart, Contained):
	response_interface = IQDictResponse

@interface.implementer(IQFillInTheBlankWithWordBankPart)
class QFillInTheBlankWithWordBankPart(QPart, QNonGradableFillInTheBlankWithWordBankPart):  # order matters

	grader_interface = IQFillInTheBlankWithWordBankGrader

	def _weight(self, result, solution):
		return result * solution.weight
