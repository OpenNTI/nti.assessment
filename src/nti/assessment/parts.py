#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Implementations and support for question parts.

.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os.path

from zope import interface

from zope.component.interfaces import ComponentLookupError

from zope.container.contained import Contained

from zope.mimetype.interfaces import mimeTypeConstraint

from zope.schema.interfaces import ConstraintNotSatisfied

from persistent import Persistent

from nti.contentfragments.interfaces import UnicodeContentFragment as _u

from nti.externalization.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured

from .interfaces import IQPart
from .interfaces import IQFilePart
from .interfaces import IQMathPart
from .interfaces import IQPartGrader
from .interfaces import IQDictResponse
from .interfaces import IQFileResponse
from .interfaces import IQMatchingPart
from .interfaces import IQOrderingPart
from .interfaces import IQConnectingPart
from .interfaces import IQNumericMathPart
from .interfaces import IQFreeResponsePart
from .interfaces import IQSymbolicMathPart
from .interfaces import IQModeledContentPart
from .interfaces import IQMultipleChoicePart
from .interfaces import IQMatchingPartGrader
from .interfaces import IQOrderingPartGrader
from .interfaces import IQSymbolicMathGrader
from .interfaces import IQModeledContentResponse
from .interfaces import IQMultipleChoicePartGrader
from .interfaces import IQFillInTheBlankShortAnswerPart
from .interfaces import IQFillInTheBlankWithWordBankPart
from .interfaces import IQFillInTheBlankShortAnswerGrader
from .interfaces import IQFillInTheBlankWithWordBankGrader
from .interfaces import IQMultipleChoiceMultipleAnswerPart
from .interfaces import IQMultipleChoiceMultipleAnswerPartGrader

from .interfaces import convert_response_for_solution

from .common import grader_for_solution_and_response

@interface.implementer(IQPart)
@WithRepr
@EqHash('content', 'hints', 'solutions', 'explanation', 
		'grader_interface', 'grader_name',
		superhash=True,
		include_type=True)
class QPart(SchemaConfigured,Persistent):
	"""
	Base class for parts. Its :meth:`grade` method will attempt to
	transform the input based on the interfaces this object
	implements, plus the interfaces of the solution, and then call the
	:meth:`_grade` method.
	"""

	#: The interface to which we will attempt to adapt ourself, the
	#: solution and the response when grading. Should be a
	#: class:`.IQPartGrader`. The response will have first been converted
	#: for the solution.
	grader_interface = IQPartGrader

	#: The name of the grader we will attempt to adapt to. Defaults to the default,
	#: unnamed, adapter
	grader_name = _u('')

	#: If non-None, then we will always attempt to convert the
	#: response to this interface before attempting to grade.
	#: In this way parts that may not have a solution
	#: can always be sure that the response is at least
	#: of an appropriate type.
	response_interface = None

	hints = ()
	solutions = ()
	content = _u('')
	explanation = _u('')

	def grade( self, response ):

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

@interface.implementer(IQMathPart)
@EqHash(include_super=True,
		include_type=True)
class QMathPart(QPart):

	def _eq_instance( self, other ):
		return isinstance(other, QMathPart)

@interface.implementer(IQSymbolicMathPart)
@EqHash(include_super=True,
		include_type=True)
class QSymbolicMathPart(QMathPart):
	grader_interface = IQSymbolicMathGrader

@interface.implementer(IQNumericMathPart)
@EqHash(include_super=True,
		include_type=True)
class QNumericMathPart(QMathPart):
	pass

@interface.implementer(IQMultipleChoicePart)
@EqHash('choices',
		include_super=True,
		include_type=True,
		superhash=True)
class QMultipleChoicePart(QPart):
	grader_interface = IQMultipleChoicePartGrader
	choices = ()

@interface.implementer(IQMultipleChoiceMultipleAnswerPart)
class QMultipleChoiceMultipleAnswerPart(QMultipleChoicePart):
	grader_interface = IQMultipleChoiceMultipleAnswerPartGrader

@interface.implementer(IQConnectingPart)
@EqHash('labels', 'values',
		include_super=True,
		superhash=True)
class QConenctingPart(QPart):
	labels = ()
	values = ()

@interface.implementer(IQMatchingPart)
class QMatchingPart(QConenctingPart):	
	grader_interface = IQMatchingPartGrader

@interface.implementer(IQOrderingPart)
class QOrderingPart(QConenctingPart):
	grader_interface = IQOrderingPartGrader
	
@interface.implementer(IQFreeResponsePart)
@EqHash(include_super=True,
		include_type=True)
class QFreeResponsePart(QPart):
	grader_name = 'LowerQuoteNormalizedStringEqualityGrader'

@interface.implementer(IQFilePart)
@EqHash('allowed_mime_types', 'allowed_extensions', 'max_file_size',
		include_super=True,
		superhash=True)
class QFilePart(QPart):

	response_interface = IQFileResponse

	allowed_mime_types = ()
	allowed_extensions = ()
	max_file_size = None

	def grade(self, response):
		response = self.response_interface(response)
		# We first check our own constraints for submission
		# and refuse to even grade if they are not met
		if not self.is_mime_type_allowed(response.value.contentType):
			raise ConstraintNotSatisfied(response.value.contentType, 'mimeType')
		if not self.is_filename_allowed( response.value.filename ):
			raise ConstraintNotSatisfied(response.value.filename, 'filename')
		if (self.max_file_size is not None and response.value.getSize() > self.max_file_size ):
			raise ConstraintNotSatisfied(response.value.getSize(), 'max_file_size')

		super(QFilePart,self).grade(response)

	def is_mime_type_allowed( self, mime_type ):
		if mime_type:
			mime_type = mime_type.lower() # only all lower case matches the production
		if (not mime_type # No input
			or not mimeTypeConstraint(mime_type) # Invalid
			or not self.allowed_mime_types ): # Empty list: all excluded
			return False

		major, minor = mime_type.split('/')
		if major == '*' or minor == '*':
			# Must be concrete
			return False

		for mt in self.allowed_mime_types:
			if mt == '*/*':
				# Total wildcard
				return True
			mt = mt.lower()
			if mt == mime_type:
				return True

			amajor, aminor = mt.split('/')

			# Wildcards are only reasonable in the minor part,
			# e.g., text/*.
			if aminor == minor or aminor == '*':
				if major == amajor:
					return True

	def is_filename_allowed( self, filename ):
		return (filename
				 and (os.path.splitext(filename.lower())[1] in self.allowed_extensions
					  or '*' in self.allowed_extensions))

@interface.implementer(IQModeledContentPart)
@EqHash(include_super=True,
		include_type=True)
class QModeledContentPart(QPart):
	response_interface = IQModeledContentResponse

@interface.implementer(IQFillInTheBlankShortAnswerPart)
class QFillInTheBlankShortAnswerPart(QPart):
	response_interface = IQDictResponse
	grader_interface = IQFillInTheBlankShortAnswerGrader

@interface.implementer(IQFillInTheBlankWithWordBankPart)
class QFillInTheBlankWithWordBankPart(QPart, Contained):
	response_interface = IQDictResponse
	grader_interface = IQFillInTheBlankWithWordBankGrader

	def _weight(self, result, solution):
		return result * solution.weight
