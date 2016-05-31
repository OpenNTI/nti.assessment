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

from zope.location.interfaces import IContained

from zope.schema.interfaces import ConstraintNotSatisfied

from persistent import Persistent

from nti.assessment.common import make_schema
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

from nti.namedfile.constraints import FileConstraints

from nti.schema.field import SchemaConfigured

from nti.schema.schema import EqHash

@WithRepr
@interface.implementer(IQNonGradablePart, IContained)
@EqHash('content', 'hints', 'explanation',
		superhash=True,
		include_type=True)
class QNonGradablePart(SchemaConfigured, Persistent):
	"""
	Base class for parts.
	"""

	__name__ = None
	__parent__ = None

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

	#: The interface to implement when this this part IS NOT randomized
	nonrandomized_interface = IQPart
	
	#: The interface to implement when this this part IS randomized
	randomized_interface = IQPart

	#: The interface to which we will attempt to adapt ourself, the
	#: solution and the response when grading a NON randomized part. Should be a
	#: class:`.IQPartGrader`. The response will have first been converted
	#: for the solution.
	grader_interface = IQPartGrader
	
	#: The interface to which we will attempt to adapt ourself, the
	#: solution and the response when grading a randomized part.
	#: The response will have first been converted for the solution.
	randomized_grader_interface = IQPartGrader

	#: The name of the grader we will attempt to adapt to. Defaults to the default,
	#: unnamed, adapter
	grader_name = _u('')

	solutions = ()

	def _get_randomzied(self):
		return self.randomized_interface.providedBy(self)
	def _set_randomized(self, nv):
		if nv and not self.randomized_interface.providedBy(self):
			interface.alsoProvides(self, self.randomized_interface)
			self._p_changed = True
		elif self.randomized_interface.providedBy(self):
			interface.noLongerProvides(self, self.randomized_interface)
			self._p_changed = True
	randomized = property(_get_randomzied, _set_randomized)
	
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

	def schema(self):
		interfaces = tuple(self.__implemented__.interfaces())
		result = make_schema( interfaces[0] )
		return result

# Math

@interface.implementer(IQNonGradableMathPart)
@EqHash(include_super=True, include_type=True)
class QNonGradableMathPart(QNonGradablePart):

	mimeType = mime_type = 'application/vnd.nextthought.assessment.nongradablemathpart'

	def _eq_instance(self, other):
		return isinstance(other, QNonGradableMathPart)

@interface.implementer(IQMathPart)
@EqHash(include_super=True, include_type=True)
class QMathPart(QPart, QNonGradableMathPart):  # order matters

	mimeType = mime_type = 'application/vnd.nextthought.assessment.mathpart'

	def _eq_instance(self, other):
		return isinstance(other, QMathPart)

@interface.implementer(IQSymbolicMathPart)
@EqHash(include_super=True, include_type=True)
class QSymbolicMathPart(QMathPart):

	mimeType = mime_type = 'application/vnd.nextthought.assessment.symbolicmathpart'
	grader_interface = IQSymbolicMathGrader

@interface.implementer(IQNumericMathPart)
@EqHash(include_super=True,
		include_type=True)
class QNumericMathPart(QMathPart):

	mimeType = mime_type = 'application/vnd.nextthought.assessment.numericmathpart'

# Multiple Choice

@interface.implementer(IQNonGradableMultipleChoicePart)
@EqHash('choices',
		include_super=True,
		include_type=True,
		superhash=True)
class QNonGradableMultipleChoicePart(QNonGradablePart):

	mimeType = mime_type = 'application/vnd.nextthought.assessment.nongradablemultiplechoicepart'
	choices = ()
	response_interface = IQTextResponse

@interface.implementer(IQMultipleChoicePart)
@EqHash('choices',
		include_super=True,
		include_type=True,
		superhash=True)
class QMultipleChoicePart(QPart, QNonGradableMultipleChoicePart):  # order matters

	mimeType = mime_type = 'application/vnd.nextthought.assessment.multiplechoicepart'
	response_interface = None
	grader_interface = IQMultipleChoicePartGrader

# Multiple Choice Multiple Answer

@interface.implementer(IQNonGradableMultipleChoiceMultipleAnswerPart)
class QNonGradableMultipleChoiceMultipleAnswerPart(QNonGradableMultipleChoicePart):

	mimeType = mime_type = 'application/vnd.nextthought.assessment.nongradablemultiplechoicemultipleanswerpart'
	response_interface = IQListResponse

@interface.implementer(IQMultipleChoiceMultipleAnswerPart)
class QMultipleChoiceMultipleAnswerPart(QMultipleChoicePart,
										QNonGradableMultipleChoiceMultipleAnswerPart):  # order matters

	mimeType = mime_type = 'application/vnd.nextthought.assessment.multiplechoicemultipleanswerpart'
	response_interface = None
	grader_interface = IQMultipleChoiceMultipleAnswerPartGrader

# Connecting

@interface.implementer(IQNonGradableConnectingPart)
@EqHash('labels', 'values',
		include_super=True,
		superhash=True)
class QNonGradableConnectingPart(QNonGradablePart):

	mimeType = mime_type = 'application/vnd.nextthought.assessment.nongradableconnectingpart'
	labels = ()
	values = ()

@interface.implementer(IQConnectingPart)
@EqHash('labels', 'values',
		include_super=True,
		superhash=True)
class QConnectingPart(QPart, QNonGradableConnectingPart):  # order matters

	mimeType = mime_type = 'application/vnd.nextthought.assessment.connectingpart'

# CS: Spelling mistake. There maybe objects stored with
# this invalid class name
import zope.deferredimport
zope.deferredimport.initialize()
zope.deferredimport.deprecated(
	"Import from QConnectingPart instead",
	QConenctingPart='nti.assessment.parts:QConnectingPart')

@interface.implementer(IQNonGradableMatchingPart)
class QNonGradableMatchingPart(QNonGradableConnectingPart):

	mimeType = mime_type = 'application/vnd.nextthought.assessment.nongradablematchingpart'

@interface.implementer(IQMatchingPart)
class QMatchingPart(QConnectingPart, QNonGradableMatchingPart):

	mimeType = mime_type = 'application/vnd.nextthought.assessment.matchingpart'
	grader_interface = IQMatchingPartGrader

@interface.implementer(IQNonGradableOrderingPart)
class QNonGradableOrderingPart(QNonGradableConnectingPart):

	mimeType = mime_type = 'application/vnd.nextthought.assessment.nongradableorderingpart'

@interface.implementer(IQOrderingPart)
class QOrderingPart(QConnectingPart, QNonGradableOrderingPart):  # order matters

	mimeType = mime_type = 'application/vnd.nextthought.assessment.orderingpart'
	grader_interface = IQOrderingPartGrader

# Free Response

@interface.implementer(IQNonGradableFreeResponsePart)
@EqHash(include_super=True,
		include_type=True)
class QNonGradableFreeResponsePart(QNonGradablePart):

	mimeType = mime_type = 'application/vnd.nextthought.assessment.nongradablefreeresponsepart'
	response_interface = IQTextResponse

@interface.implementer(IQFreeResponsePart)
@EqHash(include_super=True,
		include_type=True)
class QFreeResponsePart(QPart, QNonGradableFreeResponsePart):  # order matters

	mimeType = mime_type = 'application/vnd.nextthought.assessment.freeresponsepart'
	response_interface = None
	grader_name = 'LowerQuoteNormalizedStringEqualityGrader'

# File part

@interface.implementer(IQNonGradableFilePart)
@EqHash('allowed_mime_types', 'allowed_extensions', 'max_file_size',
		include_super=True,
		superhash=True)
class QNonGradableFilePart(QNonGradablePart, FileConstraints):  # order matters

	mimeType = mime_type = 'application/vnd.nextthought.assessment.nongradablefilepart'
	max_file_size = None
	allowed_mime_types = ()
	allowed_extensions = ()

@interface.implementer(IQFilePart)
@EqHash('allowed_mime_types', 'allowed_extensions', 'max_file_size',
		include_super=True,
		superhash=True)
class QFilePart(QPart, QNonGradableFilePart):  # order matters

	mimeType = mime_type = 'application/vnd.nextthought.assessment.filepart'
	response_interface = IQFileResponse

	def grade(self, response):
		response = self.response_interface(response)
		# We first check our own constraints for submission
		# and refuse to even grade if they are not met
		value = response.value

		if not self.is_mime_type_allowed(value.contentType):
			raise ConstraintNotSatisfied(value.contentType, 'mimeType')

		if not self.is_filename_allowed(value.filename):
			raise ConstraintNotSatisfied(value.filename, 'filename')

		if self.max_file_size is not None and value.getSize() > self.max_file_size:
			raise ConstraintNotSatisfied(value.getSize(), 'max_file_size')

		super(QFilePart, self).grade(response)

# Modeled Content

@interface.implementer(IQNonGradableModeledContentPart)
@EqHash(include_super=True,
		include_type=True)
class QNonGradableModeledContentPart(QNonGradablePart):

	mimeType = mime_type = 'application/vnd.nextthought.assessment.nongradablemodeledcontentpart'
	response_interface = IQModeledContentResponse

@interface.implementer(IQModeledContentPart)
@EqHash(include_super=True,
		include_type=True)
class QModeledContentPart(QPart, QNonGradableModeledContentPart):  # order matters

	mimeType = mime_type = 'application/vnd.nextthought.assessment.modeledcontentpart'

# Fill in the Blank

@interface.implementer(IQNonGradableFillInTheBlankShortAnswerPart)
class QNonGradableFillInTheBlankShortAnswerPart(QNonGradablePart):

	mimeType = mime_type = 'application/vnd.nextthought.assessment.nongradablefillintheblankshortanswerpart'
	response_interface = IQDictResponse

@interface.implementer(IQFillInTheBlankShortAnswerPart)
class QFillInTheBlankShortAnswerPart(QPart, QNonGradableFillInTheBlankShortAnswerPart):  # order matters

	mimeType = mime_type = 'application/vnd.nextthought.assessment.fillintheblankshortanswerpart'
	grader_interface = IQFillInTheBlankShortAnswerGrader

@interface.implementer(IQNonGradableFillInTheBlankWithWordBankPart)
class QNonGradableFillInTheBlankWithWordBankPart(QNonGradablePart, Contained):

	mimeType = mime_type = 'application/vnd.nextthought.assessment.nongradablefillintheblankwithwordbankpart'
	response_interface = IQDictResponse

@interface.implementer(IQFillInTheBlankWithWordBankPart)
class QFillInTheBlankWithWordBankPart(QPart, QNonGradableFillInTheBlankWithWordBankPart):  # order matters

	mimeType = mime_type = 'application/vnd.nextthought.assessment.fillintheblankwithwordbankpart'
	grader_interface = IQFillInTheBlankWithWordBankGrader

	def _weight(self, result, solution):
		return result * solution.weight
