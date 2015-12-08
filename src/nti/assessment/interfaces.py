#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.container.interfaces import IContained

from zope.interface.interfaces import IMethod

from zope.interface.common.mapping import IReadMapping
from zope.interface.common.mapping import IWriteMapping
from zope.interface.common.mapping import IEnumerableMapping

from zope.interface.common.sequence import IFiniteSequence

from zope.mimetype.interfaces import mimeTypeConstraint

from zope.schema import vocabulary

from dolmen.builtins.interfaces import IDict
from dolmen.builtins.interfaces import IList
from dolmen.builtins.interfaces import IString
from dolmen.builtins.interfaces import INumeric
from dolmen.builtins.interfaces import IUnicode
from dolmen.builtins.interfaces import IIterable

from nti.contentfragments.schema import Tag
from nti.contentfragments.schema import LatexFragmentTextLine as _LatexTextLine
from nti.contentfragments.schema import HTMLContentFragment as _HTMLContentFragment
from nti.contentfragments.schema import TextUnicodeContentFragment as _ContentFragment

from nti.coremetadata.interfaces import IRecordable

from nti.dataserver_core.interfaces import IContextAnnotatable
from nti.dataserver_core.interfaces import INeverStoredInSharedStream

from nti.dataserver_fragments.interfaces import ITitledContent
from nti.dataserver_fragments.schema import CompoundModeledContentBody

from nti.ntiids.schema import ValidNTIID

from nti.schema.field import Int
from nti.schema.field import Bool
from nti.schema.field import Dict
from nti.schema.field import List
from nti.schema.field import Float
from nti.schema.field import Tuple
from nti.schema.field import Choice
from nti.schema.field import Object
from nti.schema.field import Number
from nti.schema.field import Variant
from nti.schema.field import ListOrTuple
from nti.schema.field import IndexedIterable
from nti.schema.field import ValidText as Text
from nti.schema.field import ValidTextLine as TextLine
from nti.schema.field import ValidDatetime as Datetime

from nti.schema.jsonschema import TAG_HIDDEN_IN_UI
from nti.schema.jsonschema import TAG_REQUIRED_IN_UI

NTIID_TYPE = 'NAQ'
POLL_MIME_TYPE = u'application/vnd.nextthought.napoll'
SURVEY_MIME_TYPE = u'application/vnd.nextthought.nasurvey'
QUESTION_SET_MIME_TYPE = u'application/vnd.nextthought.naquestionset'

class IPollable(interface.Interface):
	"""
	marker interface for pollable parts
	"""

class IGradable(interface.Interface):
	"""
	marker interface for gradable parts
	"""

class IQHint(interface.Interface):
	"""
	Information intended to help a student complete a question.

	This may have such attributes as 'difficulty' or 'assistance level'.

	It my be inline or be a link (reference) to other content.
	"""

class IQTextHint(IQHint):
	"""
	A hint represented as text.
	"""
	value = _ContentFragment(title="The hint text")

class IQHTMLHint(IQHint):
	"""
	A hint represented as html.
	"""
	value = _HTMLContentFragment(title="The hint html")

class IQSolution(interface.Interface):

	weight = Float( title="The relative correctness of this solution, from 0 to 1",
					description="""If a question has multiple possible solutions, some may
					be more right than others. This is captured by the weight field. If there is only
					one right answer, then it has a weight of 1.0.
					""",
					min=0.0,
					max=1.0,
					default=1.0)

class IQPartSolutionsExternalizer(interface.Interface):
	"""
	marker interface to externalize a part solutions
	"""

	def to_external_object(self):
		pass

class IQResponse(IContained, INeverStoredInSharedStream):
	"""
	A response submitted by the student.
	"""

class IQTextResponse(IQResponse):
	"""
	A response submitted as text.
	"""

	value = Text(title="The response text")

class IQListResponse(IQResponse):
	"""
	A response submitted as a list.
	"""

	value = List(title="The response list",
				 min_length=1,
				 value_type=TextLine(title="The value"))

class IQDictResponse(IQResponse):
	"""
	A response submitted as a mapping between keys and values.
	"""
	value = Dict(title="The response dictionary",
				 key_type=TextLine(title="The key"),
				 value_type=TextLine(title="The value"))

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

from nti.namedfile.interfaces import INamedFile
from nti.namedfile.interfaces import IInternalFileRef

class IQUploadedFile(INamedFile):
	pass
IInternalUploadedFileRef = IInternalFileRef  # BWC

class IQFileResponse(IQResponse):
	"""
	A response containing a file and associated metadata.
	The file is uploaded as a ``data`` URI (:mod:`nti. utils. dataurl`)
	which should contain a MIME type definition;  the original
	filename may be given as well. Externalization refers to these
	two fields as
	"""

	value = Object(IQUploadedFile,
					title="The uploaded file")

# It seems like the concepts of domain and range may come into play here somewhere

class IQNonGradablePart(interface.Interface):

	content = _ContentFragment(title="The content to present to the user for this portion, if any.")

	hints = IndexedIterable(title="Any hints that pertain to this part",
							value_type=Object(IQHint, title="A hint for the part"))

class IQPart(IQNonGradablePart, IGradable):
	"""
	One generally unnumbered (or only locally numbered) portion of a :class:`Question`
	which requires a response.
	"""

	explanation = _ContentFragment(title="An explanation of how the solution is arrived at.",
									default='')

	solutions = IndexedIterable(title="Acceptable solutions for this question part in no particular order.",
								description="All solutions must be of the same type, and there must be at least one.",
								value_type=Object(IQSolution, title="A solution for this part"))

	def grade(response):
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
IQGradablePart = IQPart  # alias

class IQPartGrader(interface.Interface):
	"""
	An object that knows how to grade solutions, given a response. Should be registered
	as a multi-adapter on the question part, solution, and response types.
	"""

	def __call__():
		"""
		Implement the contract of :meth:`IQPart.grade`.
		"""

class IQSingleValuedSolution(IQSolution):
	"""
	A solution consisting of a single value.
	"""
	value = interface.Attribute("The correct value")

class IQMultiValuedSolution(IQSolution):
	"""
	A solution consisting of a set of values.
	"""
	value = List(title="The correct answer selections",
				 description="The correct answer as a tuple of items which are a zero-based index into the choices list.",
				 min_length=0,
				 value_type=TextLine(title="The value"))

# math parts

class IQNonGradableMathPart(IQNonGradablePart):
	"""
	A math question part
	"""

class IQMathPart(IQNonGradableMathPart, IQPart):
	"""
	A question part whose answer lies in the math domain.
	"""
IQGradableMathPart = IQMathPart  # alias

class IQMathSolution(IQSolution):
	"""
	A solution in the math domain. Generally intended to be abstract and
	specialized.
	"""

	allowed_units = IndexedIterable(title="Strings naming unit suffixes",
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
									value_type=TextLine(title="The unit"))

class IQNumericMathSolution(IQMathSolution, IQSingleValuedSolution):
	"""
	A solution whose correct answer is numeric in nature, and
	should be graded according to numeric equivalence.
	"""

	value = Float(title="The correct numeric answer; really an arbitrary number")

class IQSymbolicMathSolution(IQMathSolution):
	"""
	A solution whose correct answer should be interpreted symbolically.
	For example, "12Π" (twelve pi, not 37.6...) or "√2" (the square root of two, not
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

class IQLatexSymbolicMathSolution(IQSymbolicMathSolution, IQSingleValuedSolution):
	"""
	A solution whose correct answer should be interpreted
	as symbols, parsed from latex.
	"""

	value = _LatexTextLine(title="The LaTeX form of the correct answer.",
							min_length=1)

class IResponseToSymbolicMathConverter(interface.Interface):
	"""
	An object that knows how to produce a symbolic (parsed) version
	of a response. Should be registered as a multi-adapter on the
	solution and response type.
	"""

	def convert(response):
		"""
		Produce and return a symbolic version of the response.
		"""

class IQSymbolicMathGrader(IQPartGrader):
	"""
	Specialized grader for symbolic math expressions.
	"""

# multiple choice

class IQNonGradableMultipleChoicePart(IQNonGradablePart, IPollable):
	"""
	A question part that asks the student to choose between a fixed set
	of alternatives.
	"""

	choices = List(title="The choice strings to present to the user.",
					min_length=1,
					description="""Presentation order may matter, hence the list. But for grading purposes,
					the order does not matter and simple existence within the set is sufficient.""",
					value_type=_ContentFragment(title="A rendered value"))
IQNonGradableMultipleChoicePart.setTaggedValue('response_type', IQTextResponse)

class IQMultipleChoiceSolution(IQSolution, IQSingleValuedSolution):
	"""
	A solution whose correct answer is drawn from a fixed list
	of possibilities. The student is expected to choose from
	the options presented. These will typically be used in isolation as a single part.
	"""

	value = interface.Attribute("The correct answer as the zero-based index into the choices list.")

class IQMultipleChoicePart(IQNonGradableMultipleChoicePart, IQPart):

	solutions = IndexedIterable(title="The multiple-choice solutions",
								min_length=1,
								value_type=Object(IQMultipleChoiceSolution,
													title="Multiple choice solution"))
IQGradableMultipleChoicePart = IQMultipleChoicePart  # alias

class IQMultipleChoicePartGrader(IQPartGrader):
	"""
	Specialized interface for grading multiple choice questions.
	"""

# multiple choice multiple answer

class IQNonGradableMultipleChoiceMultipleAnswerPart(IQNonGradableMultipleChoicePart):
	"""
	A question part that asks the student to choose between a fixed set
	of alternatives.
	"""
IQNonGradableMultipleChoiceMultipleAnswerPart.setTaggedValue('response_type', IQListResponse)

class IQMultipleChoiceMultipleAnswerSolution(IQSolution,
											 IQMultiValuedSolution):
	"""
	A solution whose correct answer is drawn from a fixed list
	of possibilities. The student is expected to choose from
	the options presented. These will typically be used in isolation as a single part.
	"""

	value = List(title="The correct answer selections",
				 description="The correct answer as a tuple of items which are a zero-based index into the choices list.",
				 min_length=1,
				 value_type=Int(title="The value", min=0))

class IQMultipleChoiceMultipleAnswerPart(IQNonGradableMultipleChoiceMultipleAnswerPart,
										 IQMultipleChoicePart):

	solutions = IndexedIterable(title="The multiple-choice solutions",
								min_length=1,
								value_type=Object(IQMultipleChoiceMultipleAnswerSolution,
												  title="Multiple choice / multiple answer solution"))

class IQMultipleChoiceMultipleAnswerPartGrader(IQPartGrader):
	"""
	Specialized interface for grading multiple choice questions.
	"""

# free response

class IQNonGradableFreeResponsePart(IQNonGradablePart, IPollable):
	pass
IQNonGradableFreeResponsePart.setTaggedValue('response_type', IQTextResponse)

class IQFreeResponseSolution(IQSolution, IQSingleValuedSolution):
	"""
	A solution whose correct answer is simple text.
	"""

	value = Text(title="The correct text response", min_length=1)

class IQFreeResponsePart(IQNonGradableFreeResponsePart, IQPart):
	"""
	A part whose correct answer is simple text.

	These parts are intended for very short submissions.
	"""
IQGradableFreeResponsePart = IQFreeResponsePart

# connecting part

class IQNonGradableConnectingPart(IQNonGradablePart, IPollable):
	"""
	A question part that asks the student to connect items from one
	column (labels) with items in another column (values) forming a
	one-to-one and onto mapping.

	The possibilities are represented as two equal-length lists
	because order of presentation does matter, and to permit easy
	grading: responses are submitted as mapping from label position to
	value position.
	"""

	labels = List(title="The list of labels",
				  min_length=2,
				  value_type=_ContentFragment(title="A label-column value"))

	values = List(title="The list of values",
				  min_length=2,
				  value_type=_ContentFragment(title="A value-column value"))

class IQNonGradableMatchingPart(IQNonGradableConnectingPart):
	pass

class IQNonGradableOrderingPart(IQNonGradableConnectingPart):
	pass

class IQConnectingSolution(IQSolution):
	"""
	Connecting solutions are the correct mapping from keys to values.
	Generally this will be a mapping of integer locations, but it may
	also be a mapping of actual keys and values. The response is an
	IDictResponse of ints or key/values.
	"""
	value = Dict(title="The correct mapping.")

class IQMatchingSolution(IQConnectingSolution):
	pass

class IQOrderingSolution(IQConnectingSolution):
	pass

class IQConnectingPart(IQNonGradableConnectingPart, IQPart):  # BWC
	pass
IQGradableConnectingPart = IQConnectingPart  # alias

class IQMatchingPart(IQNonGradableMatchingPart, IQConnectingPart):

	solutions = IndexedIterable(title="The matching solution",
								min_length=1,
								value_type=Object(IQMatchingSolution, title="Matching solution"))

IQGradableMatchingPart = IQMatchingPart  # alias

class IQOrderingPart(IQNonGradableOrderingPart, IQConnectingPart):

	solutions = IndexedIterable(title="The matching solution",
								min_length=1,
								value_type=Object(IQOrderingSolution, title="Ordering solution"))

IQGradableOrderingPart = IQMatchingPart  # alias

class IQConnectingPartGrader(IQPartGrader):
	pass

class IQMatchingPartGrader(IQConnectingPartGrader):
	"""
	A grader for matching questions.
	"""

class IQOrderingPartGrader(IQConnectingPartGrader):
	"""
	A grader for ordering questions.
	"""

# file part

class IQNonGradableFilePart(IQNonGradablePart):
	"""
	A part that requires the student to upload a file from their own
	computer.

	In this interface you specify MIME types and/or
	filename extensions that can be used as input. If the incoming
	data matches any of the types or extensions, it will be allowed.
	To allow anything (unwise), include "*/*" in the ``allowed_mime_types``
	or include "*" in the ``allowed_extensions``.
	"""

	allowed_mime_types = IndexedIterable(title="Mime types that are accepted for upload",
										 min_length=1,
										 value_type=Text(title="An allowed mimetype",
													 	 constraint=mimeTypeConstraint))

	allowed_extensions = IndexedIterable(title="Extensions like '.doc' that are accepted for upload",
										 min_length=0,
										 value_type=Text(title="An allowed extension"))

	max_file_size = Int(title="Maximum size in bytes for the file",
						min=1,
						required=False)

	def is_mime_type_allowed(mime_type):
		"""
		Return whether or not the given mime type, which must match
		the mime type constraint, is one of the allowed types of this
		part, taking into account wildcards.
		"""

	def is_filename_allowed(filename):
		"""
		Return whether the filename given is allowed according to
		the allowed list of extensions.
		"""

class IQFilePart(IQNonGradableFilePart, IQPart):
	"""
	Note that this part cannot be automatically graded
	(hence there is no corresponding solution), it can merely be
	routed to a responsible party for grading manually.
	"""
IQGradableFilePart = IQFilePart  # alias

# modeled content part

class IQNonGradableModeledContentPart(IQNonGradablePart, IPollable):
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

class IQModeledContentPart(IQNonGradableModeledContentPart, IQPart):
	pass

IQGradableModeledContentPart = IQModeledContentPart

# assessment

class IQAssessment(interface.Interface):
	"""
	Marker interface for all assessment objects
	"""

# question

class IQuestion(IQAssessment, IAttributeAnnotatable):
	"""
	A question consists of one or more parts (typically one) that require answers.
	It may have prefacing text. It may have other metadata, such as what
	concepts it relates to (e.g., Common Core Standards numbers); such concepts
	will be domain specific.

	Questions are annotatable. Uses of this include things like references
	to where questions appear in question sets or other types of content.
	"""

	ntiid = ValidNTIID(title="Question NTIID", required=False)

	content = Text(title="The content to present to the user, if any.",
					default='')

	parts = IndexedIterable(title="The ordered parts of the question.",
							min_length=1,
							value_type=Object(IQPart, title="A question part") )

class IQuestionSet(IQAssessment, ITitledContent, IAttributeAnnotatable):
	"""
	An ordered group of related questions generally intended to be
	completed as a unit (aka, a Quiz or worksheet).

	Question sets are annotatable; Uses of this include things like
	references to where question sets are defined in content or
	which assignments reference them.
	"""

	ntiid = ValidNTIID(title="Question set NTIID", required=False)

	questions = IndexedIterable(title="The ordered questions in the set.",
								description="For convenience, this should also be aliased to `parts`",
								min_length=1,
								value_type=Object(IQuestion, title="The questions") )
	
	def __len__():
		"""
		return the number of questions in this set
		"""

class IQAssignmentPart(ITitledContent):
	"""
	One portion of an assignment.
	"""

	content = Text(title="Additional content for the question set in the context of an assignment.",
					default='')

	question_set = Object(IQuestionSet,
						  title="The question set to submit with this part")

	auto_grade = Bool(title="Should this part be run through the grading machinery?",
					  default=False)

class IQSubmittable(IRecordable):

	available_for_submission_beginning = Datetime(
		title="Submissions are accepted no earlier than this.",
		description="""When present, this specifies the time instant at which
		submissions of this object may begin to be accepted. If this is absent,
		submissions are always allowed. While this is represented here as an actual
		concrete timestamp, it is expected that in many cases the source representation
		will be relative to something else (a ``timedelta``) and conversion to absolute
		timestamp will be done as needed.""",
		required=False)

	available_for_submission_ending = Datetime(
		title="Submissions are accepted no later than this.",
		description="""When present, this specifies the last instance at which
		submissions will be accepted. It can be considered the object's "due date."
		As with ``available_for_submission_beginning``,
		this will typically be relative and converted.""",
		required=False)

	no_submit = Bool(title="Whether this object accept submissions",
					 default=False)

class IQAssignment(IQAssessment, ITitledContent, IAttributeAnnotatable, IQSubmittable):
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

	ntiid = ValidNTIID(title="Assignment NTIID", required=False)

	content = Text(title="The content to present to the user, if any.",
					default='')

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

	parts = ListOrTuple(title="The ordered parts of the assignment.",
						description="""Unlike questions, assignments with zero parts are allowed.
						Because they accept no input, such an assignment is very
						special and serves as a marker to higher levels of code.
						""",
						min_length=0,
						value_type=Object(IQAssignmentPart, title="An assignment part"))

	is_non_public = Bool(title="Whether this assignment should be public or restricted",
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

IQAssignment['title'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQAssignment['title'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQAssignment['available_for_submission_ending'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQAssignment['available_for_submission_ending'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQAssignment['available_for_submission_beginning'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQAssignment['available_for_submission_beginning'].setTaggedValue(TAG_REQUIRED_IN_UI, False)

class IQTimedAssignment(IQAssignment):

	maximum_time_allowed = Int(	title="Maximum Time Allowed (Seconds)",
						 		description="""When present, this specifies the maximum time allowed (in
								seconds) students have to submit the assignments""",
								required=True)

IQTimedAssignment['title'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQTimedAssignment['title'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQTimedAssignment['available_for_submission_ending'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQTimedAssignment['available_for_submission_ending'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQTimedAssignment['available_for_submission_beginning'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQTimedAssignment['available_for_submission_beginning'].setTaggedValue(TAG_REQUIRED_IN_UI, False)

class IQAssessmentDateContext(interface.Interface):
	"""
	An object that can be used as context to adapt an assessment
	date.

	This package provides no implementations of this interface.
	"""

	def assessments():
		"""
		return the list of assessment ids in this context
		"""
	assignments = assessments  # alias for BWC

	def of(assessment):
		"""
		Given an assessment, return an object having the same date
		attributes as the assessment, but interpreted in the context
		of this object. If no changes are required, can return the assessment
		itself.
		"""
	
	def set(assessment, name, value):
		"""
		Set the attribute value for the specified assessment
		"""
IQAssignmentDateContext = IQAssessmentDateContext  # alias for BWC

class IQAssessmentPolicies(interface.Interface):

	"""
	An object that can be used to hold (uninterpreted) policy
	objects keyed off of assignment NTIIDs.

	This package defines no implementations of this interface.
	"""

	def getPolicyForAssessment(assignment_ntiid):
		"""
		Return a policy object for the assessment.
		"""
	getPolicyForAssignment = getPolicyForAssessment  # alias for BWC

	def assessments():
		"""
		return the list of assessments ids in this object
		"""
	assignments = assessments  # alias for BWC

	def size():
		"""
		return the number of assessments
		"""

	def clear():
		"""
		clear all policies
		
		:return true if policies were cleared
		"""

	def __bool__():
		"""
		Are there any policies registered? If no, return False.
		"""

IQAssignmentPolicies = IQAssessmentPolicies  # alias for BWC

class IQAssessmentPolicyValidator(interface.Interface):
	"""
	An object that can be validate an assessment policy
	"""

	def validate(assessment_ntiid, policy):
		"""
		validates the specfied policy.
		"""

IQAssignmentPolicyValidator = IQAssessmentPolicyValidator # alias for BWC

# set solutions response types

IQMathSolution.setTaggedValue('response_type', IQTextResponse)
IQMatchingSolution.setTaggedValue('response_type', IQDictResponse)
IQOrderingSolution.setTaggedValue('response_type', IQDictResponse)
IQFreeResponseSolution.setTaggedValue('response_type', IQTextResponse)
IQMultipleChoiceSolution.setTaggedValue('response_type', IQTextResponse)
IQMultipleChoiceMultipleAnswerSolution.setTaggedValue('response_type', IQListResponse)

def convert_response_for_solution(solution, response):
	"""
	Given a solution and a response, attempt to adapt
	the response to the type needed by the grader.
	Uses the `response_type` tagged value on the interfaces implemented
	by the grader.
	"""
	if not IQSolution.providedBy(solution):
		# Well, nothing to be done, no info given
		return response

	for iface in interface.providedBy(solution).flattened():
		response_type = iface.queryTaggedValue('response_type')
		if response_type:
			result = response_type(response, alternate=None)  # adapt or return if already present
			if result is not None:
				response = result
				break
	return response

# Objects having to do with the assessment process itself.
# There is a three part lifecycle: The source object,
# the submission, and finally the assessed value. The three
# parts have similar structure.

class IQBaseSubmission(IContained):
	"""
	The root of the tree for submission objects.
	"""

	CreatorRecordedEffortDuration = Number(
		title="A fractional count of seconds spent creating the submission",
		description="If desired, the creator (i.e., external client) can "
		"optionally track the amount of time spent creating the submission and "
		"submit it here with the initial submission; after that it is immutable and "
		"(currently) unseen. NOTE: Because this is tracked and submitted by the client, "
		"it is NOT suitable to use for any actual assessment purposes such as imposing time "
		"limits.",
		min=0.0,
		required=False,
		readonly=True,
		default=None)

	CreatorRecordedEffortDuration.setTaggedValue('_ext_allow_initial_set', True)
	# This is documented as not being available for public consumption,
	# but if we enforce that, we also are not able to automatically read it on creation,
	# because `nti.externalization.datastructures.InterfaceObjectIO``
	# collapses the two concepts into one.

class IQPartsSubmission(IQBaseSubmission):

	parts = IndexedIterable(title="Ordered submissions, one for each part of the poll.",
							default=(),
							description="""The length must match the length of the questions. Each object must be
							adaptable into the proper :class:`IQResponse` object (e.g., a string or dict).""")

class IQuestionSubmission(IQPartsSubmission):
	"""
	A student's submission in response to a question.

	These will typically be transient objects.
	"""

	questionId = TextLine(title="Identifier of the question being responded to.")

class IQSubmittedPart(IContained):
	"""
	The submitted value of a single part.

	These will generally be persistent values that are echoed back to clients.
	"""

	# In the past, updating from external objects transformed the
	# value into an IQResponse (because this was an Object field of
	# that type)...but the actual assessment code itself assigned the
	# raw string/int value. Responses would be ideal, but that could
	# break existing client code. The two behaviours are now unified
	# because of using a field property, so this Variant now documents
	# the types that clients were actually seeing on the wire.
	submittedResponse = Variant((Object(IString),
								 Object(INumeric),
								 Object(IDict),
								 Object(IList),
								 Object(IUnicode),
								 Object(IQUploadedFile),
								 Object(IQModeledContentResponse),  # List this so we get specific validation for it
								 Object(IQResponse)),
								 variant_raise_when_schema_provided=True,
								 title="The response as the student submitted it, or None if they skipped",
								 required=False,
								 default=None)

class IQAssessedPart(IQSubmittedPart):
	"""
	The assessed value of a single part.

	"""
	# TODO: Matching to question?

	assessedValue = Float(title="The relative correctness of the submitted response, from 0.0 (entirely wrong) to 1.0 (perfectly correct)",
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

	questionId = TextLine(title="Identifier of the question being responded to.")
	parts = IndexedIterable(title="Ordered assessed values, one for each part of the question.",
							value_type=Object(IQAssessedPart, title="The assessment of a part."))


class IQuestionSetSubmission(IQBaseSubmission):
	"""
	A student's submission in response to an entire question set.

	These will generally be transient objects.
	"""

	questionSetId = TextLine(title="Identifier of the question set being responded to.")
	questions = IndexedIterable(title="Submissions, one for each question in the set.",
								 description="""Order is not important. Depending on the question set,
								 missing answers may or may not be allowed; the set may refuse to grade, or simply consider them wrong.""",
								 default=(),
								 value_type=Object(IQuestionSubmission,
													title="The submission for a particular question."))

class IQAssessedQuestionSet(IContained, IContextAnnotatable):
	"""
	The assessed value of a student's submission to an entire question set.

	These will usually be persistent values that are also echoed back to clients.
	"""

	questionSetId = TextLine(title="Identifier of the question set being responded to.")
	questions = IndexedIterable(title="Assessed questions, one for each question in the set.",
								value_type=Object(IQAssessedQuestion,
												  title="The assessed value for a particular question."))

class IQAssignmentSubmission(IQBaseSubmission):
	"""
	A student's submission in response to an assignment.
	"""

	assignmentId = TextLine(title="Identifier of the assignment being responded to.")
	parts = IndexedIterable(title="Question set submissions, one for each part of the assignment.",
							description="""Order is not significant, each question set will be matched
							with the corresponding part by ID. However, each part *must* have a
							submission.""",
							default=(),
							value_type=Object(IQuestionSetSubmission,
											  title="The submission for a particular part."))

class IQAssignmentSubmissionPendingAssessment(IQBaseSubmission):
	"""
	A submission for an assignment that cannot be completely assessed;
	complete assessment is pending. This is typically the step after
	submission and before completion.
	"""

	assignmentId = TextLine(title="Identifier of the assignment being responded to.")
	parts = IndexedIterable(title="Either an assessed question set, or the original submission",
							value_type=Variant(
								 (Object(IQAssessedQuestionSet),
								  Object(IQuestionSetSubmission))))

class IQAssessmentItemContainer(IEnumerableMapping):
	"""
	Something that is an unordered bag of assessment items (such as
	questions, question sets, and assignments).

	This package provides no implementation of this interface. (But
	something like the content library package may be adaptable to this,
	typically with annotations).
	"""
		
	def assessments():
		"""
		return an iterable with all assessmentsi this container
		"""

# fill-in-the-blank part

class IQNonGradableFillInTheBlankPart(IQNonGradablePart):
	"""
	Marker interface for a Fill-in-the-blank question part.
	"""

class IQFillInTheBlankPart(IQNonGradableFillInTheBlankPart, IQPart):
	"""
	Marker interface for a Fill-in-the-blank question part.
	"""
IQGradableFillInTheBlankPart = IQFillInTheBlankPart

# fill-in-the-blank short answer part

class IQNonGradableFillInTheBlankShortAnswerPart(IQNonGradableFillInTheBlankPart):
	pass

class IQFillInTheBlankShortAnswerGrader(IQPartGrader):
	pass

class IRegEx(interface.Interface):
	pattern = TextLine(title="the pattern")
	solution = _ContentFragment(title="A solution to present to the user.",
								required=False)

class IQFillInTheBlankShortAnswerSolution(IQSolution):

	value = Dict(key_type=TextLine(title="input name/id"),
				 value_type=Variant((TextLine(title="The pattern"),
									 Object(IRegEx, title="The regex object")),
									 title="The correct regex"),
				 title="The correct answer regexes",
				 description="The correct word id map.",
				 min_length=1)

IQFillInTheBlankShortAnswerSolution.setTaggedValue('response_type', IQDictResponse)

class IQFillInTheBlankShortAnswerPart(IQNonGradableFillInTheBlankShortAnswerPart,
									  IQFillInTheBlankPart):
	"""
	Marker interface for a Fill-in-the-blank short answer question part.
	"""

	solutions = IndexedIterable(title="The solutions",
								min_length=1,
								value_type=Object(IQFillInTheBlankShortAnswerSolution,
												  title="the solution"))

class IQFillInTheBlankWithWordBankGrader(IQPartGrader):
	pass

class IQFillInTheBlankWithWordBankSolution(IQSolution):

	value = Dict(key_type=TextLine(title="input name/id"),
				 value_type=Variant((TextLine(title="word id answer"),
									  ListOrTuple(TextLine(title="word id answer"))),
									title="The word ids"),
				 title="The correct answer selections",
				 description="The correct word id map.",
				 min_length=1)

IQFillInTheBlankWithWordBankSolution.setTaggedValue('response_type', IQDictResponse)

# fill-in-the-blank with word bank part

class IWordEntry(interface.Interface):
	wid = TextLine(title="word identifier")
	word = TextLine(title="the word")
	lang = TextLine(title="language identifier", default="en", required=False)
	content = _ContentFragment(title="The input to present to the user.", required=False)

class IWordBank(IIterable, IReadMapping):

	entries = List(title="The word entries",
				   value_type=Object(IWordEntry, title="The word"),
				   min_length=1)

	unique = Bool(title="A word can be used once in a question/part",
				  default=True, required=False)

class IQNonGradableFillInTheBlankWithWordBankPart(IQFillInTheBlankPart):
	"""
	Marker interface for a Fill-in-the-blank with word bank question part.
	If the word bank is not specified it would the one from the parent question
	"""

	wordbank = Object(IWordBank, required=False,
					  title="The wordbank to present to the user.")

	input = _ContentFragment(title="The input to present to the user.")

class IQFillInTheBlankWithWordBankPart(IQNonGradableFillInTheBlankWithWordBankPart,
									   IQFillInTheBlankPart):

	solutions = IndexedIterable(title="The solutions",
								min_length=1,
								value_type=Object(IQFillInTheBlankWithWordBankSolution,
												  title="the solution"))

class IQFillInTheBlankWithWordBankQuestion(IQuestion):
	"""
	Marker interface for a Fill-in-the-blank with word bank question.

	The word bank for the question may be used by any question parts
	"""
	wordbank = Object(IWordBank, required=False)

	parts = IndexedIterable(title="The ordered parts of the question.",
							min_length=1,
							value_type=Object(IQFillInTheBlankWithWordBankPart,
											  title="A question part"))

# Normalizer

class IQPartResponseNormalizer(interface.Interface):
	"""
	A marker interface for an adapter that that knows how to normalize a given
	:class:`IQResponse` for a :class:`IQNonGradablePart`
	"""

	def __call__():
		pass

class IQFreeResponsePartResponseNormalizer(IQPartResponseNormalizer):
	"""
	A marker interface for an adapter that that knows how to normalize a given
	a :class:`IQResponse` for a :class:`IQNonGradablePart`
	"""

class IQModeledContentPartResponseNormalizer(IQPartResponseNormalizer):
	"""
	A marker interface for an adapter that that knows how to normalize a given
	a :class:`IQResponse` for a :class:`IQNonGradableModeledContentPart`
	"""

class IQMultipleChoicePartResponseNormalizer(IQPartResponseNormalizer):
	"""
	A marker interface for an adapter that that knows how to normalize a given
	a :class:`IQResponse` for a :class:`IQNonGradableMultipleChoicePart`
	"""

class IQMultipleChoiceMultipleAnswerPartResponseNormalizer(IQPartResponseNormalizer):
	"""
	A marker interface for an adapter that that knows how to normalize a given
	a :class:`IQResponse` for a :class:`IQNonGradableMultipleChoiceMultipleAnswerPart`
	"""

class IQMatchingPartResponseNormalizer(IQPartResponseNormalizer):
	"""
	A marker interface for an adapter that that knows how to normalize a given
	a :class:`IQResponse` for a :class:`IQNonGradableMatchingPart`
	"""
	
class IQOrderingPartResponseNormalizer(IQPartResponseNormalizer):
	"""
	A marker interface for an adapter that that knows how to normalize a given
	a :class:`IQResponse` for a :class:`IQNonGradableOrderingPart`
	"""

# polls

DISCLOSURE_NEVER = u'never'
DISCLOSURE_ALWAYS = u'always'
DISCLOSURE_TERMINATION = u'termination'

DISCLOSURE_STATES = (DISCLOSURE_NEVER, DISCLOSURE_ALWAYS, DISCLOSURE_TERMINATION)
DISCLOSURE_VOCABULARY = vocabulary.SimpleVocabulary([vocabulary.SimpleTerm(_x) for _x in DISCLOSURE_STATES])

class IQInquiry(IAttributeAnnotatable, IQSubmittable):

	ntiid = ValidNTIID(title="Object NTIID", required=False)

	disclosure = Choice(vocabulary=DISCLOSURE_VOCABULARY, title='Disclosure policy',
					 	required=True, default=DISCLOSURE_TERMINATION)

	closed = Bool(title="Close flag", required=False, default=False)
	closed.setTaggedValue('_ext_excluded_out', True)
	
	no_submit = Bool(title="Whether this object accept submissions",
					 default=False, required=False)
	no_submit.setTaggedValue('_ext_excluded_out', True)
	
class IQPoll(IQInquiry, IFiniteSequence):
	"""
	A poll question consists of one or more parts (typically one).
	It may have prefacing text. It may have other metadata, such as what
	concepts it relates to (e.g., Common Core Standards numbers); such concepts
	will be domain specific.

	Polls are annotatable. Uses of this include things like references
	to where questions appear in question sets or other types of content.
	"""

	content = Text(title="The content to present to the user, if any.",
				   default='', required=False)

	parts = IndexedIterable(title="The ordered parts of the question.",
							min_length=1,
							value_type=Object(IPollable, title="A pollable question part") )

IQPoll['available_for_submission_ending'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQPoll['available_for_submission_ending'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQPoll['available_for_submission_beginning'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQPoll['available_for_submission_beginning'].setTaggedValue(TAG_REQUIRED_IN_UI, False)

class IQSurvey(ITitledContent, IQInquiry, IFiniteSequence):
	"""
	An ordered group of poll questions.

	Surveys sets are annotatable.
	"""

	questions = IndexedIterable(title="The ordered polls in the set.",
								min_length=1,
								value_type=Object(IQPoll, title="The poll questions") )
	
	def __len__():
		"""
		return the number of questions in this survey
		"""

IQPoll['available_for_submission_ending'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQPoll['available_for_submission_ending'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQPoll['available_for_submission_beginning'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQPoll['available_for_submission_beginning'].setTaggedValue(TAG_REQUIRED_IN_UI, False)

class IQInquirySubmission(IQPartsSubmission):
	inquiryId = interface.Attribute("Identifier of the inquiry being responded to.")
	inquiryId.setTaggedValue('_ext_excluded_out', True)

class IQPollSubmission(IQInquirySubmission):
	"""
	A submission in response to a poll.

	These will typically be transient objects.
	"""

	pollId = TextLine(title="Identifier of the poll being responded to.")

class IQSurveySubmission(IQInquirySubmission, IContextAnnotatable, IWriteMapping):
	"""
	A submission in response to a survey
	"""

	surveyId = TextLine(title="Identifier of the survey being responded to.")
	questions = IndexedIterable(title="Submissions, one for each poll in the survey.",
								default=(),
								value_type=Object(IQPollSubmission,
												  title="The submission for a particular poll."))

class IQAggregatedPartFactory(interface.Interface):
	
	def __call__():
		pass

class IQAggregatedPart(IContained):

	Total = interface.Attribute("Aggregated part total")
	Results = interface.Attribute("Aggregated part results")

	def reset():
		"""
		reset this part
		"""

	def append(response):
		"""
		Aggregate the specified response
		"""

	def __iadd__(other):
		pass

class IQAggregatedConnectingPart(IQAggregatedPart):

	Results = Dict( title="The response results",
				 	key_type=Tuple(title="The response tuples",
								   min_length=1,
				 				   value_type=Tuple(title="The choices")),
				 	value_type=Number(title="The aggregated value"),
				 	readonly=True)

class IQAggregatedMatchingPart(IQAggregatedConnectingPart):
	pass
	
class IQAggregatedOrderingPart(IQAggregatedConnectingPart):
	pass

class IQAggregatedMultipleChoicePart(IQAggregatedPart):

	Results = Dict( title="The response results",
				 	key_type=Int(title="The choice index"),
				 	value_type=Number(title="The aggregated value"),
				 	readonly=True)

class IQAggregatedMultipleChoiceMultipleAnswerPart(IQAggregatedMultipleChoicePart):

	Results = Dict( title="The response results",
				 	key_type=Tuple(title="The response tuple",
								   min_length=1,
				 				   value_type=Int(title="The choice indices")),
				 	value_type=Number(title="The aggregated value"),
				 	readonly=True)

class IQAggregatedFreeResponsePart(IQAggregatedPart):

	Results = Dict( title="The response results",
				 	key_type=TextLine(title="the value"),
				 	value_type=Number(title="The aggregated value"),
				 	readonly=True)

class IQAggregatedModeledContentPart(IQAggregatedPart):

	Results = List(title="The response results",
				   value_type=Object(IQModeledContentResponse),
				   readonly=True)

class IQAggregatedInquiry(IContained, IContextAnnotatable):

	id = interface.Attribute("Identifier of the inquiry being aggregated.")
	id.setTaggedValue('_ext_excluded_out', True)

	def __iadd__(other):
		pass

class IQAggregatedPoll(IQAggregatedInquiry, IIterable, IFiniteSequence):
	"""
	Aggregation for a poll
	"""

	pollId = TextLine(title="Identifier of the poll being aggregated.")
	parts = IndexedIterable(title="Part aggregations.",
							default=(),
							value_type=Object(IQAggregatedPart,
											  title="The aggregated part."))

class IQAggregatedSurvey(IQAggregatedInquiry, IIterable, IWriteMapping):
	"""
	Aggregation for a survey
	"""

	surveyId = TextLine(title="Identifier of the survey being aggregated.")
	questions = IndexedIterable(title="Poll aggregations.",
								default=(),
							 	value_type=Object(IQAggregatedPoll,
												  title="The aggregated poll."))

ASSESSMENT_INTERFACES = (IQAssignment, IQuestion, IQuestionSet, IQPoll, IQSurvey)

def _set_ifaces():
	for iSchema in ASSESSMENT_INTERFACES:
		for k, v in iSchema.namesAndDescriptions(all=True):
			if IMethod.providedBy(v) or v.queryTaggedValue(TAG_HIDDEN_IN_UI) is not None:
				continue
			iSchema[k].setTaggedValue(TAG_HIDDEN_IN_UI, True)

_set_ifaces()
del _set_ifaces
