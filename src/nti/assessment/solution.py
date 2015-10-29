#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from persistent import Persistent

from nti.externalization.representation import WithRepr

from nti.schema.schema import EqHash

from .parts import QPart
from .parts import QMatchingPart
from .parts import QOrderingPart
from .parts import QNumericMathPart
from .parts import QFreeResponsePart
from .parts import QSymbolicMathPart
from .parts import QMultipleChoicePart
from .parts import QFillInTheBlankShortAnswerPart
from .parts import QFillInTheBlankWithWordBankPart
from .parts import QMultipleChoiceMultipleAnswerPart

from .interfaces import IQSolution
from .interfaces import IQMathSolution
from .interfaces import IQMatchingSolution
from .interfaces import IQOrderingSolution
from .interfaces import IQConnectingSolution
from .interfaces import IQNumericMathSolution
from .interfaces import IQFreeResponseSolution
from .interfaces import IQSymbolicMathSolution
from .interfaces import IQMultipleChoiceSolution
from .interfaces import IQLatexSymbolicMathSolution
from .interfaces import IQFillInTheBlankShortAnswerSolution
from .interfaces import IQFillInTheBlankWithWordBankSolution
from .interfaces import IQMultipleChoiceMultipleAnswerSolution

from ._util import TrivialValuedMixin as _TrivialValuedMixin

@WithRepr
@interface.implementer(IQSolution)
class QSolution(Persistent):
	"""
	Base class for solutions. Its :meth:`grade` method
	will attempt to transform the input based on the interfaces
	this object implements and then call the :meth:`.QPart.grade` method.
	"""
	#: Defines the factory used by the :meth:`grade` method to construct
	#: a :class:`.IQPart` object. Also, instances are only equal if this value
	#: is equal
	_part_type = QPart

	weight = 1.0

	def grade( self, response ):
		"""
		Convenience method for grading solutions that can be graded independent
		of their question parts.
		"""
		return self._part_type(solutions=(self,)).grade(response)

@interface.implementer(IQMathSolution)
class QMathSolution(QSolution):
	"""
	Base class for the math hierarchy.
	"""
	allowed_units = None # No defined unit handling

	def __init__( self, *args, **kwargs ):
		super(QMathSolution,self).__init__()
		allowed_units = args[1] if len(args) > 1 else kwargs.get('allowed_units')
		if allowed_units is not None:
			self.allowed_units = allowed_units # TODO: Do we need to defensively copy?

@EqHash('_part_type', 'weight', 'value',
		superhash=True)
class _EqualityValuedMixin(_TrivialValuedMixin):
	pass

@interface.implementer(IQNumericMathSolution)
class QNumericMathSolution(_EqualityValuedMixin, QMathSolution):
	"""
	Numeric math solution.

	.. todo:: This grading mechanism is pretty poorly handled and compares
		by exact equality.
	"""
	_part_type = QNumericMathPart

@interface.implementer(IQFreeResponseSolution)
class QFreeResponseSolution(_EqualityValuedMixin, QSolution):
	"""
	Simple free-response solution.
	"""
	_part_type = QFreeResponsePart

@interface.implementer(IQSymbolicMathSolution)
class QSymbolicMathSolution(QMathSolution):
	"""
	Symbolic math grading is redirected through
	grading components for extensibility.
	"""
	_part_type = QSymbolicMathPart

@interface.implementer(IQLatexSymbolicMathSolution)
class QLatexSymbolicMathSolution(_EqualityValuedMixin, QSymbolicMathSolution):
	"""
	The answer is defined to be in latex.
	"""
	# TODO: Verification of the value? Minor transforms like adding $$?

@interface.implementer(IQConnectingSolution)
class QConenctionSolution(_EqualityValuedMixin, QSolution):
	pass

@interface.implementer(IQMatchingSolution)
class QMatchingSolution(QConenctionSolution):
	_part_type = QMatchingPart

@interface.implementer(IQOrderingSolution)
class QOrderingSolution(QConenctionSolution):
	_part_type = QOrderingPart
	
@interface.implementer(IQMultipleChoiceSolution)
class QMultipleChoiceSolution(_EqualityValuedMixin, QSolution):
	_part_type = QMultipleChoicePart

@interface.implementer(IQMultipleChoiceMultipleAnswerSolution)
class QMultipleChoiceMultipleAnswerSolution(_EqualityValuedMixin, QSolution):
	"""
	The answer is defined as a list of selections which best represent
	the correct answer.
	"""
	_part_type = QMultipleChoiceMultipleAnswerPart

@interface.implementer(IQFillInTheBlankShortAnswerSolution)
class QFillInTheBlankShortAnswerSolution(_EqualityValuedMixin, QSolution):
	_part_type = QFillInTheBlankShortAnswerPart

@interface.implementer(IQFillInTheBlankWithWordBankSolution)
class QFillInTheBlankWithWordBankSolution(_EqualityValuedMixin, QSolution):
	_part_type = QFillInTheBlankWithWordBankPart
