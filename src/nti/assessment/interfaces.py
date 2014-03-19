#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
$Id$
"""
from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

import re

from zope import interface
from zope.interface.common import mapping
from zope.interface.common import sequence
from zope.mimetype.interfaces import mimeTypeConstraint

from zope.container.interfaces import IContained
from zope.annotation.interfaces import IAnnotatable

from nti.utils.schema import Bool
from nti.utils.schema import ValidDatetime as Datetime
from nti.utils.schema import Dict
from nti.utils.schema import Float
from nti.utils.schema import IndexedIterable
from nti.utils.schema import Int
from nti.utils.schema import List
from nti.utils.schema import ListOrTuple
from nti.utils.schema import Object
from nti.utils.schema import Variant
from nti.utils.schema import ValidText as Text
from nti.utils.schema import ValidTextLine as TextLine

from dolmen.builtins.interfaces import IDict
from dolmen.builtins.interfaces import IList
from dolmen.builtins.interfaces import INumeric
from dolmen.builtins.interfaces import IString
from dolmen.builtins.interfaces import IUnicode
from dolmen.builtins.interfaces import IIterable

NTIID_TYPE = 'NAQ'

from nti.contentfragments.schema import LatexFragmentTextLine as _LatexTextLine
from nti.contentfragments.schema import HTMLContentFragment as _HTMLContentFragment
from nti.contentfragments.schema import TextUnicodeContentFragment as _ContentFragment


from nti.dataserver.interfaces import CompoundModeledContentBody
from nti.dataserver.interfaces import INeverStoredInSharedStream
from nti.dataserver.interfaces import ITitledContent
from nti.dataserver.interfaces import ILastModified
from nti.dataserver.interfaces import Tag


from nti.monkey import plonefile_zopefile_patch_on_import
plonefile_zopefile_patch_on_import.patch()

class IQHint(interface.Interface):
	"""
	Information intended to help a student complete a question.

	This may have such attributes as 'difficulty' or 'assistance level'.

	It my be inline or be a link (reference) to other content.
	"""
	# TODO: Model this better

class IQTextHint(IQHint):
	"""
	A hint represented as text.
	"""
	value = _ContentFragment( title="The hint text" )

class IQHTMLHint(IQHint):
	"""
	A hint represented as html.
	"""
	value = _HTMLContentFragment( title="The hint html" )

class IQSolution(interface.Interface):

	weight = Float( title="The relative correctness of this solution, from 0 to 1",
					description="""If a question has multiple possible solutions, some may
					be more right than others. This is captured by the weight field. If there is only
					one right answer, then it has a weight of 1.0.
					""",
					min=0.0,
					max=1.0,
					default=1.0 )

# It seems like the concepts of domain and range may come into play here,
# somewhere

class IQPart(interface.Interface):
	"""
	One generally unnumbered (or only locally numbered) portion of a :class:`Question`
	which requires a response.
	"""

	content = _ContentFragment( title="The content to present to the user for this portion, if any." )
	hints = IndexedIterable( title="Any hints that pertain to this part",
							 value_type=Object(IQHint, title="A hint for the part") )
	solutions = IndexedIterable( title="Acceptable solutions for this question part in no particular order.",
								 description="All solutions must be of the same type, and there must be at least one.",
								 value_type=Object(IQSolution, title="A solution for this part")	)
	explanation = _ContentFragment( title="An explanation of how the solution is arrived at.",
									default='' )

	def grade( response ):
		"""
		Determine the correctness of the given response. Usually this will do its work
		by delegating to a registered :class:`IQPartGrader`.

		:param response: An :class:`IResponse` object representing the student's input for this
			part of the question. If the response is an inappropriate type for the part,
			an exception may be raised.
		:return: A value that can be interpreted as a boolean, indicating correct (``True``) or incorrect
			(``False``) response. A return value of ``None`` indicates no opinion, typically because
			there are no provided solutions. If solution weights are
			taken into account, this will be a floating point number between 0.0 (incorrect) and 1.0 (perfect).
		"""

class IQMathPart(IQPart):
	"""
	A question part whose answer lies in the math domain.
	"""

class IQPartGrader(interface.Interface):
	"""
	An object that knows how to grade solutions, given a response. Should be registered
	as a multi-adapter on the question part, solution, and response types.
	"""

	def __call__( ):
		"""
		Implement the contract of :meth:`IQPart.grade`.
		"""

class IQSingleValuedSolution(IQSolution):
	"""
	A solution consisting of a single value.
	"""
	value = interface.Attribute( "The correct value" )


class IQMultiValuedSolution(IQSolution):
	"""
	A solution consisting of a set of values.
	"""
	value = List( title="The correct answer selections",
				  description="The correct answer as a tuple of items which are a zero-based index into the choices list.",
				  min_length=0,
				  value_type=TextLine( title="The value" ) )

class IQMathSolution(IQSolution):
	"""
	A solution in the math domain. Generally intended to be abstract and
	specialized.
	"""

	allowed_units = IndexedIterable( title="Strings naming unit suffixes",
									 description="""
									 Numbers or expressions may have units. Sometimes the correct
									 answer depends on the correct unit being applied; sometimes the unit is optional,
									 and sometimes there must not be a unit (it is a dimensionless quantity).

									 If this attribute is ``None`` (the default) no special handling of units
									 is attempted.

									 If this attribute is an empty sequence, no units are accepted.

									 If this attribute consists of one or more strings, those are units to accept.
									 Include the empty string (last) to make units optional.""",
									 min_length=0,
									 required=False,
									 value_type=TextLine( title="The unit" ) )

class IQNumericMathSolution(IQMathSolution,IQSingleValuedSolution):
	"""
	A solution whose correct answer is numeric in nature, and
	should be graded according to numeric equivalence.
	"""

	value = Float( title="The correct numeric answer; really an arbitrary number" )

class IQSymbolicMathSolution(IQMathSolution):
	"""
	A solution whose correct answer should be interpreted symbolically.
	For example, "12π" (twelve pi, not 37.6...) or "√2" (the square root of two, not
	1.4...).

	This is intended to be further subclassed to support specific types of
	symbolic interpretation.
	"""

class IQSymbolicMathPart(IQMathPart):
	"""
	A part whose solutions are symbolic math.
	"""

class IQNumericMathPart(IQMathPart):
	"""
	A part whose solutions are numeric math.
	"""

class IQLatexSymbolicMathSolution(IQSymbolicMathSolution,IQSingleValuedSolution):
	"""
	A solution whose correct answer should be interpreted
	as symbols, parsed from latex.
	"""

	value = _LatexTextLine( title="The LaTeX form of the correct answer.",
							min_length=1 )

class IResponseToSymbolicMathConverter(interface.Interface):
	"""
	An object that knows how to produce a symbolic (parsed) version
	of a response. Should be registered as a multi-adapter on the
	solution and response type.
	"""

	def convert( response ):
		"""
		Produce and return a symbolic version of the response.
		"""

class IQSymbolicMathGrader(IQPartGrader):
	"""
	Specialized grader for symbolic math expressions.
	"""

class IQMultipleChoiceSolution(IQSolution,IQSingleValuedSolution):
	"""
	A solution whose correct answer is drawn from a fixed list
	of possibilities. The student is expected to choose from
	the options presented. These will typically be used in isolation as a single part.
	"""

	value = interface.Attribute( "The correct answer as the zero-based index into the choices list." )

class IQMultipleChoicePart(IQPart):
	"""
	A question part that asks the student to choose between a fixed set
	of alternatives.
	"""

	choices = List( title="The choice strings to present to the user.",
					min_length=1,
					description="""Presentation order may matter, hence the list. But for grading purposes,
					the order does not matter and simple existence within the set is sufficient.""",
					value_type=_ContentFragment( title="A rendered value" ) )
	solutions = IndexedIterable( title="The multiple-choice solutions",
								 min_length=1,
								 value_type=Object( IQMultipleChoiceSolution, title="Multiple choice solution" ) )

class IQMultipleChoicePartGrader(IQPartGrader):
	"""
	Specialized interface for grading multiple choice questions.
	"""


class IQMultipleChoiceMultipleAnswerSolution(IQSolution,IQMultiValuedSolution):
	"""
	A solution whose correct answer is drawn from a fixed list
	of possibilities. The student is expected to choose from
	the options presented. These will typically be used in isolation as a single part.
	"""

	value = List( title="The correct answer selections",
				  description="The correct answer as a tuple of items which are a zero-based index into the choices list.",
				  min_length=1,
				  value_type=Int( title="The value",
								  min=0) )


class IQMultipleChoiceMultipleAnswerPart(IQMultipleChoicePart):
	"""
	A question part that asks the student to choose between a fixed set
	of alternatives.
	"""

	solutions = IndexedIterable( title="The multiple-choice solutions",
								 min_length=1,
								 value_type=Object( IQMultipleChoiceMultipleAnswerSolution, title="Multiple choice / multiple answer solution" ) )


class IQMultipleChoiceMultipleAnswerPartGrader(IQPartGrader):
	"""
	Specialized interface for grading multiple choice questions.
	"""


class IQFreeResponseSolution(IQSolution,IQSingleValuedSolution):
	"""
	A solution whose correct answer is simple text.
	"""

	value = Text( title="The correct text response", min_length=1 )

class IQFreeResponsePart(IQPart):
	"""
	A part whose correct answer is simple text.

	These parts are intended for very short submissions.
	"""

class IQMatchingSolution(IQSolution):
	"""
	Matching solutions are the correct mapping from keys to values.
	Generally this will be a mapping of integer locations, but it may
	also be a mapping of actual keys and values. The response is an
	IDictResponse of ints or key/values.
	"""

	value = Dict( title="The correct mapping." )

class IQMatchingPart(IQPart):
	"""
	A question part that asks the student to connect items from one
	column (labels) with items in another column (values) forming a
	one-to-one and onto mapping.

	The possibilities are represented as two equal-length lists
	because order of presentation does matter, and to permit easy
	grading: responses are submitted as mapping from label position to
	value position.
	"""

	labels = List( title="The list of labels",
				   min_length=2,
				   value_type=_ContentFragment( title="A label-column value" ) )
	values = List( title="The list of values",
				   min_length=2,
				   value_type=_ContentFragment( title="A value-column value" ) )
	solutions = IndexedIterable( title="The matching solution",
								 min_length=1,
								 value_type=Object( IQMatchingSolution, title="Matching solution" ) )

class IQMatchingPartGrader(IQPartGrader):
	"""
	A grader for matching questions.
	"""

class IQFilePart(IQPart):
	"""
	A part that requires the student to upload a file from their own
	computer. Note that this part cannot be automatically graded
	(hence there is no corresponding solution), it can merely be
	routed to a responsible party for grading manually.

	In this interface you specify MIME types and/or
	filename extensions that can be used as input. If the incoming
	data matches any of the types or extensions, it will be allowed.
	To allow anything (unwise), include "*/*" in the ``allowed_mime_types``
	or include "*" in the ``allowed_extensions``.
	"""

	allowed_mime_types = IndexedIterable( title="Mime types that are accepted for upload",
										  min_length=1,
										  value_type=Text(title="An allowed mimetype",
														  constraint=mimeTypeConstraint) )
	allowed_extensions = IndexedIterable( title="Extensions like '.doc' that are accepted for upload",
										  min_length=0,
										  value_type=Text(title="An allowed extension") )

	max_file_size = Int( title="Maximum size in bytes for the file",
						 min=1,
						 required=False )

	def is_mime_type_allowed( mime_type ):
		"""
		Return whether or not the given mime type, which must match
		the mime type constraint, is one of the allowed types of this
		part, taking into account wildcards.
		"""

	def is_filename_allowed( filename ):
		"""
		Return whether the filename given is allowed according to
		the allowed list of extensions.
		"""

class IQModeledContentPart(IQPart):
	"""
	A part intended for \"essay\" style submissions
	of rich content authored on the platform. These
	will typically be much longer than :class:`IQFreeResponsePart`.

	Currently, there are no length minimum or maximums
	defined or enforced. Likewise, there are no enforcements
	of the type of body parts that should be allowed (e.g., don't
	allow whiteboards, force a whiteboard). Those can be added
	if needed.
	"""

class IQuestion(IAnnotatable):
	"""
	A question consists of one or more parts (typically one) that require answers.
	It may have prefacing text. It may have other metadata, such as what
	concepts it relates to (e.g., Common Core Standards numbers); such concepts
	will be domain specific.

	Questions are annotatable. Uses of this include things like references
	to where questions appear in question sets or other types of content.
	"""

	content = Text( title="The content to present to the user, if any.",
					default='')
	parts = IndexedIterable( title="The ordered parts of the question.",
							 min_length=1,
							 value_type=Object( IQPart, title="A question part" ),
							 )

class IQuestionSet(ITitledContent,IAnnotatable):
	"""
	An ordered group of related questions generally intended to be
	completed as a unit (aka, a Quiz or worksheet).

	Question sets are annotatable; Uses of this include things like
	references to where question sets are defined in content or
	which assignments reference them.
	"""

	questions = IndexedIterable( title="The ordered questions in the set.",
								 min_length=1,
								 value_type=Object( IQuestion, title="The questions" ),
								 )

class IQAssignmentPart(ITitledContent):
	"""
	One portion of an assignment.
	"""

	content = Text( title="Additional content for the question set in the context of an assignment.",
					default='')

	question_set = Object(IQuestionSet,
						  title="The question set to submit with this part")
	auto_grade = Bool(title="Should this part be run through the grading machinery?",
					  default=False)

class IQAssignment(ITitledContent,
				   IAnnotatable):
	"""
	An assignment differs from either plain questions or question sets
	in that there is an expectation that it must be completed,
	typically within a set portion of time, and that completion will
	be reviewed by some other entity (such as a course teacher or
	teaching assistant, or by peers; this is context specific and
	beyond the scope of this package). A (*key*) further difference is that,
	unlike questions and question sets, assignments are *not* intended
	to be used by reference. Each assignment is a unique object appearing
	exactly once within the content tree.

	An assignment is a collection of one or more assignment parts that
	are all submitted together. Each assignment part holds a question
	set, and whether or not the submission of that question set should
	be automatically assessed (keeping in mind that some types of questions
	cannot be automatically assessed).

	Submitting an assignment will fail if: not all parts have
	submissions (or the submitted part does not match the correct
	question set); if the submission window is not open (too early; too
	late is left to the discretion of the professor); the assignment
	has been submitted before.

	When an assignment is submitted, each auto-gradeable part is
	graded. Any remaining parts are left alone; events are emitted to
	alert the appropriate entity that grading needs to take place.

	Assignments are annotatable: Uses of this include things like references to
	where assignments are defined in content.
	"""

	content = Text( title="The content to present to the user, if any.",
					default='')

	available_for_submission_beginning = Datetime(
		title="Submissions are accepted no earlier than this.",
		description="""When present, this specifies the time instant at which
		submissions of this assignment may begin to be accepted. If this is absent,
		submissions are always allowed. While this is represented here as an actual
		concrete timestamp, it is expected that in many cases the source representation
		will be relative to something else (a ``timedelta``) and conversion to absolute
		timestamp will be done as needed.""",
		required=False)
	available_for_submission_ending = Datetime(
		title="Submissions are accepted no later than this.",
		description="""When present, this specifies the last instance at which
		submissions will be accepted. It can be considered the assignment's "due date."
		As with ``available_for_submission_beginning``,
		this will typically be relative and converted.""",
		required=False )

	category_name = Tag(title="Assignments can be grouped into categories.",
						description="""By providing this information, assignments
						can be grouped by an additional dimension. This grouping
						might be used for display purposes (such as in a gradebook)
						or even for calculation purposes (each different category contributes
						differently to the final grade).

						Currently this is limited to an arbitrary tag value;
						in the future it might either become more constrained
						to a set of supported choices or broaden to support an entire
						line of text, depending on use.

						A convention may evolve to allow UIs to recognize
						and display particular categories specially (for example,
						course-level assignments like participation or attendance
						or final grade). That should be documented here.
						""",
						default='default',
						required=True)

	parts = ListOrTuple( title="The ordered parts of the assignment.",
						 description="""Unlike questions, assignments with zero parts are allowed.
						 Because they accept no input, such an assignment is very
						 special and serves as a marker to higher levels of code.
						 """,
						 min_length=0,
						 value_type=Object( IQAssignmentPart,
											title="An assignment part" ) )

	is_non_public = Bool( title="Whether this assignment should be public or restricted",
						  description="""An ill-defined semi-layer violation. Set it to true if
						  this should somehow be non-public and not available to everyone. This
						  is the default. Specific applications will determine what should and should
						  not be public""",
						  default=True)

	# A note on handling assignments that have an associated time limit
	# (e.g., you have one hour to complete this assignment once you begin):
	# That information will be encoded as a timedelta on the assignment.
	# The server will accept an "open" request for the assignment and make a
	# note of the time stamp. When submission is attempted, the server
	# will check that the assignment has been opened, and the elapsed time.
	# Depending on the policy and context, submission will either be blocked,
	# or the elapsed time will simply be recorded.



class IQResponse(IContained,
				 INeverStoredInSharedStream):
	"""
	A response submitted by the student.
	"""

class IQTextResponse(IQResponse):
	"""
	A response submitted as text.
	"""

	value = Text( title="The response text" )

class IQListResponse(IQResponse):
	"""
	A response submitted as a list.
	"""

	value = List( title="The response list",
				  min_length=1,
				  value_type=TextLine(title="The value") )

class IQDictResponse(IQResponse):
	"""
	A response submitted as a mapping between keys and values.
	"""
	value = Dict( title="The response dictionary",
				  key_type=TextLine( title="The key" ),
				  value_type=TextLine(title="The value") )


class IQModeledContentResponse(IQResponse,
							   ITitledContent):
	"""
	A response with a value similar to that of a conventional
	Note, consisting of multiple parts and allowing for things
	like embedded whiteboards and the like.

	Unlike other response types, this one must be submitted
	in its proper external form as this type object, not a primitive.
	"""

	value = CompoundModeledContentBody()
	value.required = True
	value.__name__ = 'value'


import plone.namedfile.interfaces
class IQUploadedFile(plone.namedfile.interfaces.INamedFile,ILastModified):
	pass

class IQFileResponse(IQResponse):
	"""
	A response containing a file and associated metadata.
	The file is uploaded as a ``data`` URI (:mod:`nti. utils. dataurl`)
	which should contain a MIME type definition;  the original
	filename may be given as well. Externalization refers to these
	two fields as
	"""

	value = Object( IQUploadedFile,
					title="The uploaded file" )


IQMathSolution.setTaggedValue( 'response_type', IQTextResponse )
IQFreeResponseSolution.setTaggedValue( 'response_type', IQTextResponse )
IQMultipleChoiceSolution.setTaggedValue( 'response_type', IQTextResponse )
IQMultipleChoiceMultipleAnswerSolution.setTaggedValue( 'response_type', IQListResponse )
IQMatchingSolution.setTaggedValue( 'response_type', IQDictResponse )

def convert_response_for_solution(solution, response):
	"""
	Given a solution and a response, attempt to adapt
	the response to the type needed by the grader.
	Uses the `response_type` tagged value on the interfaces implemented
	by the grader.
	"""
	if not IQSolution.providedBy( solution ):
		# Well, nothing to be done, no info given
		return response

	for iface in interface.providedBy( solution ).flattened():
		response_type = iface.queryTaggedValue( 'response_type' )
		if response_type:
			result = response_type( response, alternate=None ) # adapt or return if already present
			if result is not None:
				response = result
				break

	return response

###
# Objects having to do with the assessment process itself.
# There is a three part lifecycle: The source object,
# the submission, and finally the assessed value. The three
# parts have similar structure.
###

class IQuestionSubmission(IContained):
	"""
	A student's submission in response to a question.

	These will typically be transient objects.
	"""

	questionId = TextLine( title="Identifier of the question being responded to." )
	parts = IndexedIterable( title="Ordered submissions, one for each part of the question.",
							 default=(),
							 description="""The length must match the length of the questions. Each object must be
							 adaptable into the proper :class:`IQResponse` object (e.g., a string or dict).""" )


class IQAssessedPart(IContained):
	"""
	The assessed value of a single part.

	These will generally be persistent values that are echoed back to clients.
	"""
	# TODO: Matching to question?

	# In the past, updating from external objects transformed the
	# value into an IQResponse (because this was an Object field of
	# that type)...but the actual assessment code itself assigned the
	# raw string/int value. Responses would be ideal, but that could
	# break existing client code. The two behaviours are now unified
	# because of using a field property, so this Variant now documents
	# the types that clients were actually seeing on the wire.
	submittedResponse = Variant( (Object(IString),
								  Object(INumeric),
								  Object(IDict),
								  Object(IList),
								  Object(IUnicode),
								  Object(IQUploadedFile),
								  Object(IQModeledContentResponse), # List this so we get specific validation for it
								  Object(IQResponse)),
								 variant_raise_when_schema_provided=True,
								 title="The response as the student submitted it, or None if they skipped",
								 required=False,
								 default=None)
	assessedValue = Float( title="The relative correctness of the submitted response, from 0.0 (entirely wrong) to 1.0 (perfectly correct)",
						   description="A value of None means that it was not possible to assess this part.",
						   min=0.0,
						   max=1.0,
						   default=0.0,
						   required=False)

class IQAssessedQuestion(IContained):
	"""
	The assessed value of a student's submission for a single question.

	These will typically be persistent values, echoed back to clients.
	"""

	questionId = TextLine( title="Identifier of the question being responded to." )
	parts = IndexedIterable( title="Ordered assessed values, one for each part of the question.",
							 value_type=Object( IQAssessedPart, title="The assessment of a part." ) )


class IQuestionSetSubmission(IContained):
	"""
	A student's submission in response to an entire question set.

	These will generally be transient objects.
	"""

	questionSetId = TextLine( title="Identifier of the question set being responded to." )
	questions = IndexedIterable( title="Submissions, one for each question in the set.",
								 description="""Order is not important. Depending on the question set,
								 missing answers may or may not be allowed; the set may refuse to grade, or simply consider them wrong.""",
								 default=(),
								 value_type=Object( IQuestionSubmission, title="The submission for a particular question.") )

class IQAssessedQuestionSet(IContained):
	"""
	The assessed value of a student's submission to an entire question set.

	These will usually be persistent values that are also echoed back to clients.
	"""

	questionSetId = TextLine( title="Identifier of the question set being responded to." )
	questions = IndexedIterable( title="Assessed questions, one for each question in the set.",
								 value_type=Object( IQAssessedQuestion, title="The assessed value for a particular question.") )

class IQAssignmentSubmission(IContained):
	"""
	A student's submission in response to an assignment.
	"""

	assignmentId = TextLine(title="Identifier of the assignment being responded to.")
	parts = IndexedIterable( title="Question set submissions, one for each part of the assignment.",
							 description="""Order is not significant, each question set will be matched
							 with the corresponding part by ID. However, each part *must* have a
							 submission.""",
							 default=(),
							 value_type=Object(IQuestionSetSubmission,
											   title="The submission for a particular part.") )
	#parts.setTaggedValue( '_ext_excluded_out', True ) # Internal use only

	# TODO: What does the result of submitting an assignment look like?
	# It's not always an `Assessed` object, because not all parts will have been
	# assessed in all cases.

class IQAssignmentSubmissionPendingAssessment(IContained):
	"""
	A submission for an assignment that cannot be completely assessed;
	complete assessment is pending. This is typically the step after
	submission and before completion.
	"""

	assignmentId = TextLine(title="Identifier of the assignment being responded to.")
	parts = IndexedIterable( title="Either an assessed question set, or the original submission",
							 value_type=Variant(
								 (Object(IQAssessedQuestionSet),
								  Object(IQuestionSetSubmission))) )
	#parts.setTaggedValue( '_ext_excluded_out', True ) # Internal use only


class IQAssessmentItemContainer(sequence.IReadSequence):
	"""
	Something that is an unordered bag of assessment items (such as
	questions, question sets, and assignments).

	This package provides no implementation of this interface. (But
	something like the content library package may be adaptable to this,
	typically with annotations).
	"""

# Alibra

class IWordEntry(interface.Interface):
	wid = TextLine(title="word identifier")
	word = TextLine(title="the word")
	lang = TextLine(title="language identifier", default="en", required=False)

class IWordBank(IIterable, mapping.IReadMapping):

	entries = Dict(title="The response dictionary",
				   key_type=TextLine(title="The word identifier"),
				   value_type=Object(IWordEntry, title="The word"),
				   min_length=1)

	unique = Bool(title="A word can be used once in a question/part",
				  default=True)

class IQFillInTheBlankPart(IQPart):
	"""
	Marker interface for a Fill-in-the-blank question part.
	"""

class IQFillInTheBlankShortAnswerGrader(IQPartGrader):
	pass

class IRegularExpression(interface.Interface):
	pattern = TextLine(title='the pattern', default='*')
	flags = Int(title='the regex flags', default=re.U | re.I | re.M, required=False)

class IQFillInTheBlankShortAnswerSolution(IQMultiValuedSolution):

	value = List(title="The correct answer regexes",
				 description="The correct regex",
				 min_length=0,
				 value_type=Object(IRegularExpression, title="The regular expression"))

class IQFillInTheBlankShortAnswerPart(IQFillInTheBlankPart):
	"""
	Marker interface for a Fill-in-the-blank short answer question part.
	"""
	solutions = IndexedIterable(title="The solutions",
								min_length=1,
								value_type=Object(IQFillInTheBlankShortAnswerSolution, title="the solution"))

class IQFillInTheBlankShortAnswerQuestion(IQuestion):
	pass

class IQFillInTheBlankWithWordBankGrader(IQPartGrader):
	pass

class IQFillInTheBlankWithWordBankSolution(IQMultiValuedSolution):

	value = List(title="The correct answer selections",
				 description="The correct word id.",
				 min_length=0,
				 value_type=TextLine(title="The word id"))

class IQFillInTheBlankWithWordBankPart(IQFillInTheBlankPart):
	"""
	Marker interface for a Fill-in-the-blank with word bank question part.
	If the word bank is not specified it would the one from the parent question
	"""
	wordbank = Object(IWordBank, required=False,
					  title="The wordbank to present to the user.")

	solutions = IndexedIterable(title="The solutions",
								min_length=1,
								value_type=Object(IQFillInTheBlankWithWordBankSolution, title="the solution"))

class IQFillInTheBlankWithWordBankQuestion(IQuestion):
	"""
	Marker interface for a Fill-in-the-blank with word bank question.

	The word bank for the question may be used by any question parts
	"""
	wordbank = Object(IWordBank, required=False)

