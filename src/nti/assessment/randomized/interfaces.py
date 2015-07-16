#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from nti.schema.field import Int
from nti.schema.field import Bool
from nti.schema.field import Object
from nti.schema.field import ListOrTuple

from ..interfaces import IQPart
from ..interfaces import IQPartGrader
from ..interfaces import IQuestionSet
from ..interfaces import IQMatchingPart
from ..interfaces import IQOrderingPart
from ..interfaces import IQConnectingPart
from ..interfaces import IQMatchingPartGrader
from ..interfaces import IQOrderingPartGrader
from ..interfaces import IQMultipleChoicePart
from ..interfaces import IQMultipleChoicePartGrader
from ..interfaces import IQMultipleChoiceMultipleAnswerPart
from ..interfaces import IQMultipleChoiceMultipleAnswerPartGrader

# marker

class ISha224Randomized(interface.Interface):
	"""
	marker interface to use the following generator

	hexdigest = hashlib.sha224(bytes(uid)).hexdigest()
	generator = random.Random(long(hexdigest, 16))

	where uid is the user int id
	"""

# parts

class IQRandomizedPart(IQPart):
	pass

class ISha224RandomizedPart(IQRandomizedPart, ISha224Randomized):
	pass

class IQRandomizedPartGrader(IQPartGrader):

	def unshuffle(value, user=None, context=None):
		"""
		unrandomize the specified value
		"""

# connecting part

class IQRandomizedConnectingPart(IQRandomizedPart, IQConnectingPart):
	pass

class INonRandomizedConnectingPart(IQRandomizedConnectingPart):
	pass

class ISha224RandomizedConnectingPart(IQRandomizedConnectingPart, ISha224Randomized):
	pass

# matching part

class IQRandomizedMatchingPart(IQRandomizedConnectingPart, IQMatchingPart):
	pass

class IQRandomizedMatchingPartGrader(IQMatchingPartGrader, IQRandomizedPartGrader):
	pass

class INonRandomizedMatchingPart(IQRandomizedMatchingPart):
	pass

class ISha224RandomizedMatchingPart(IQRandomizedMatchingPart, ISha224RandomizedPart):
	pass

# ordering

class IQRandomizedOrderingPart(IQRandomizedConnectingPart, IQOrderingPart):
	pass

class IQRandomizedOrderingPartGrader(IQOrderingPartGrader, IQRandomizedPartGrader):
	pass

class INonRandomizedOrderingPart(IQRandomizedOrderingPart):
	pass

class ISha224RandomizedOrderingPart(IQRandomizedOrderingPart, ISha224RandomizedPart):
	pass

# multiple choice

class IQRandomizedMultipleChoicePart(IQRandomizedPart, IQMultipleChoicePart):
	pass

class IQRandomizedMultipleChoicePartGrader(IQMultipleChoicePartGrader, IQRandomizedPartGrader):
	pass

class INonRandomizedMultipleChoicePart(IQRandomizedMultipleChoicePart):
	pass

class ISha224RandomizedMultipleChoicePart(IQRandomizedMultipleChoicePart, ISha224RandomizedPart):
	pass

# multiple choice, multiple answer

class IQRandomizedMultipleChoiceMultipleAnswerPart(IQRandomizedPart,
												   IQMultipleChoiceMultipleAnswerPart):
	pass

class IQRandomizedMultipleChoiceMultipleAnswerPartGrader(IQMultipleChoiceMultipleAnswerPartGrader,
														 IQRandomizedPartGrader):
	pass

class INonRandomizedMultipleChoiceMultipleAnswerPart(IQRandomizedMultipleChoiceMultipleAnswerPart):
	pass

class ISha224RandomizedMultipleChoiceMultipleAnswerPart(IQRandomizedMultipleChoiceMultipleAnswerPart,
														ISha224RandomizedPart):
	pass

# question set

class IRandomizedQuestionSet(IQuestionSet):
	pass

class INonRandomizedQuestionSet(IRandomizedQuestionSet):
	pass

class ISha224RandomizedQuestionSet(IRandomizedQuestionSet, ISha224Randomized):
	pass

# question bank

class IQuestionIndexRange(interface.Interface):
	start = Int(title="start index range", min=0, required=True)
	end = Int(title="end index range", min=0, required=True)
	draw = Int(title="number of questions to draw in range", min=1, required=True,
			   default=1)

class IQuestionBank(IQuestionSet):
	"""
	An group of questions taken at random

	A maximum total of questions of the question set is drawn to be presented and evaluated.
	"""

	draw = Int(title="number of questions to be randomly drawn", min=1,
				required=True, default=1)

	ranges = ListOrTuple(Object(IQuestionIndexRange), title="Question index ranges",
						 required=False, default=())

	srand = Bool(title="always use a different random seed.", required=False,
				 default=False)

	def copy(questions=None, ranges=None, srand=None):
		"""
		make a copy of this object w/ possibly new questions and/or ranges
		"""

	def copyTo(target, questions=None, ranges=None, srand=None,):
		"""
		make a copy of this object w/ possibly new questions and/or ranges to
		target
		"""

class INonRandomizedQuestionBank(IQuestionBank):
	"""
	Marker interface to avoid randomizing an question bank
	"""

class ISha224RandomizedQuestionBank(IQuestionBank, ISha224Randomized):
	pass

# Principal utility

class IPrincipalSeedSelector(interface.Interface):
	"""
	Defines a utility function to return a random seed for a pricipal
	"""

	def __call__(principal):
		"""
		return a random seed for the specified principal
		"""
