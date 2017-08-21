#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.container.interfaces import IContained

from zope.interface.common.mapping import IReadMapping
from zope.interface.common.mapping import IWriteMapping
from zope.interface.common.mapping import IEnumerableMapping

from zope.interface.common.sequence import IFiniteSequence

from zope.interface.interfaces import IObjectEvent

from zope.interface.interfaces import ObjectEvent

from zope.lifecycleevent import ObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

from zope.schema import vocabulary

from nti.base.interfaces import IDict
from nti.base.interfaces import IList
from nti.base.interfaces import INumeric
from nti.base.interfaces import IIterable

from nti.contentfragments.interfaces import IString
from nti.contentfragments.interfaces import IUnicode

from nti.contentfragments.schema import Tag
from nti.contentfragments.schema import LatexFragmentTextLine as _LatexTextLine
from nti.contentfragments.schema import HTMLContentFragment as _HTMLContentFragment
from nti.contentfragments.schema import TextUnicodeContentFragment as _ContentFragment

from nti.contenttypes.reports.interfaces import IReportContext

from nti.coremetadata.interfaces import IVersioned
from nti.coremetadata.interfaces import ITitledContent
from nti.coremetadata.interfaces import IContextAnnotatable

from nti.coremetadata.interfaces import IObjectJsonSchemaMaker
from nti.coremetadata.interfaces import INeverStoredInSharedStream

from nti.coremetadata.schema import ExtendedCompoundModeledContentBody

from nti.mimetype.mimetype import rfc2047MimeTypeConstraint

from nti.ntiids.schema import ValidNTIID

from nti.property.property import alias

from nti.publishing.interfaces import IPublishable
from nti.publishing.interfaces import INoPublishLink
from nti.publishing.interfaces import ICalendarPublishable

from nti.recorder.interfaces import IRecordable
from nti.recorder.interfaces import IRecordableContainer

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
from nti.schema.field import Iterable
from nti.schema.field import ListOrTuple
from nti.schema.field import IndexedIterable
from nti.schema.field import ValidText as Text
from nti.schema.field import ValidTextLine as TextLine
from nti.schema.field import ValidDatetime as Datetime

from nti.schema.jsonschema import TAG_HIDDEN_IN_UI
from nti.schema.jsonschema import TAG_REQUIRED_IN_UI

NTIID_TYPE = u'NAQ'
PART_NTIID_TYPE = u'NAQPart'

POLL_MIME_TYPE = 'application/vnd.nextthought.napoll'
SURVEY_MIME_TYPE = 'application/vnd.nextthought.nasurvey'
QUESTION_MIME_TYPE = 'application/vnd.nextthought.naquestion'
QUESTION_SET_MIME_TYPE = 'application/vnd.nextthought.naquestionset'
QUESTION_BANK_MIME_TYPE = 'application/vnd.nextthought.naquestionbank'
ASSIGNMENT_MIME_TYPE = 'application/vnd.nextthought.assessment.assignment'
TIMED_ASSIGNMENT_MIME_TYPE = 'application/vnd.nextthought.assessment.timedassignment'
RANDOMIZED_QUESTION_SET_MIME_TYPE = 'application/vnd.nextthought.narandomizedquestionset'
DISCUSSION_ASSIGNMENT_MIME_TYPE = 'application/vnd.nextthought.assessment.discussionassignment'
QUESTION_FILL_IN_THE_BLANK_MIME_TYPE = 'application/vnd.nextthought.naquestionfillintheblankwordbank'

ASSESSMENT_MIME_TYPES = (QUESTION_MIME_TYPE,
                         ASSIGNMENT_MIME_TYPE,
                         QUESTION_SET_MIME_TYPE,
                         QUESTION_BANK_MIME_TYPE,
                         TIMED_ASSIGNMENT_MIME_TYPE,
                         DISCUSSION_ASSIGNMENT_MIME_TYPE,
                         RANDOMIZED_QUESTION_SET_MIME_TYPE,
                         QUESTION_FILL_IN_THE_BLANK_MIME_TYPE)

INQUIRY_MIME_TYPES = (POLL_MIME_TYPE, SURVEY_MIME_TYPE)

ALL_ASSIGNMENT_MIME_TYPES = (ASSIGNMENT_MIME_TYPE,
                             TIMED_ASSIGNMENT_MIME_TYPE,
                             DISCUSSION_ASSIGNMENT_MIME_TYPE)

ALL_EVALUATION_MIME_TYPES = ASSESSMENT_MIME_TYPES + INQUIRY_MIME_TYPES


class IRegEx(interface.Interface):
    pattern = TextLine(title=u"the pattern")
    solution = _ContentFragment(title=u"A solution to present to the user.",
                                required=False)


class IQEvaluation(IContained):
    """
    marker interface for evaluation objects
    """
    __home__ = interface.Attribute("home location")
    __home__.setTaggedValue('_ext_excluded_out', True)

    tags = ListOrTuple(TextLine(title=u"A single tag"), required=False)
IQEvaluation.setTaggedValue('_ext_jsonschema', u'')
IQEvaluation.setTaggedValue('_ext_is_marker_interface', True)


class IQEvaluationItemContainer(IContained):
    """
    marker interface for evaluation object containers
    """

    Items = Iterable(title=u'All the resolved items in this container',
                     readonly=True, required=False)
    Items.setTaggedValue('_ext_excluded_out', True)

    def __len__():
        """
        return the number of items in this container
        """

    def remove(obj):
        """
        remove the specifed object from this container
        """
IQEvaluationItemContainer.setTaggedValue('_ext_is_marker_interface', True)


class IPollable(interface.Interface):
    """
    marker interface for pollable parts
    """
IPollable.setTaggedValue('_ext_is_marker_interface', True)


class IGradable(interface.Interface):
    """
    marker interface for gradable parts
    """
IGradable.setTaggedValue('_ext_is_marker_interface', True)


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
    value = _ContentFragment(title=u"The hint text")


class IQHTMLHint(IQHint):
    """
    A hint represented as html.
    """
    value = _HTMLContentFragment(title=u"The hint html")


class IQSolution(interface.Interface):

    weight = Number(title=u"The relative correctness of this solution, from 0 to 1",
                    description=u"""If a question has multiple possible solutions, some may
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

    value = Text(title=u"The response text")


class IQListResponse(IQResponse):
    """
    A response submitted as a list.
    """

    value = List(title=u"The response list",
                 min_length=1,
                 value_type=TextLine(title=u"The value"))


class IQDictResponse(IQResponse):
    """
    A response submitted as a mapping between keys and values.
    """
    value = Dict(title=u"The response dictionary",
                 key_type=TextLine(title=u"The key"),
                 value_type=TextLine(title=u"The value"))


class IQModeledContentResponse(IQResponse,
                               ITitledContent):
    """
    A response with a value similar to that of a conventional
    Note, consisting of multiple parts and allowing for things
    like embedded whiteboards and the like.

    Unlike other response types, this one must be submitted
    in its proper external form as this type object, not a primitive.
    """

    value = ExtendedCompoundModeledContentBody()
    value.required = True
    value.__name__ = u'value'


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

    value = Object(IQUploadedFile, title=u"The uploaded file")


# It seems like the concepts of domain and range may come into play here
# somewhere


class IQNonGradablePart(interface.Interface):

    content = _ContentFragment(title=u"The content to present to the user for this portion, if any.")

    hints = IndexedIterable(title=u"Any hints that pertain to this part",
                            value_type=Object(IQHint,
                                              title=u"A hint for the part"),
                            required=False)


class IQPartGrader(interface.Interface):
    """
    An object that knows how to grade solutions, given a response. Should be registered
    as a multi-adapter on the question part, solution, and response types.
    """

    def __call__():
        """
        Implement the contract of :meth:`IQPart.grade`.
        """


class IQPart(IQNonGradablePart, IGradable):
    """
    One generally unnumbered (or only locally numbered) portion of a :class:`Question`
    which requires a response.
    """

    explanation = _ContentFragment(title=u"An explanation of how the solution is arrived at.",
                                   default=u'',
                                   required=False)

    solutions = IndexedIterable(title=u"Acceptable solutions for this question part in no particular order.",
                                description=u"All solutions must be of the same type, and there must be at least one.",
                                value_type=Object(IQSolution,
                                                  title=u"A solution for this part"),
                                min_length=0,
                                required=False)

    randomized = Bool(title=u"Boolean to indicate whether this part is randomized.",
                      default=False,
                      required=False)

    weight = Number(title=u"The relative point value of this part, compared to other parts.",
                    description=u"""When calculating points per part, the weight is used to
                    calculate what part of a :class:`IQuestion` total_points goes towards
                    this part.
                    """,
                    min=0.0,
                    max=1.0,
                    default=1.0)

    def grade(response, creator=None):
        """
        Determine the correctness of the given response. Usually this will do its work
        by delegating to a registered :class:`IQPartGrader`.

        :param response: An :class:`IResponse` object representing the student's input for this
                part of the question. If the response is an inappropriate type for the part,
                an exception may be raised.
        :param response: An :class:`IPrincipal` object representing the user taking the
                assessment. May be necessary for accurate grading.
        :return: A value that can be interpreted as a boolean, indicating correct (``True``) or incorrect
                (``False``) response. A return value of ``None`` indicates no opinion, typically because
                there are no provided solutions. If solution weights are
                taken into account, this will be a floating point number between 0.0 (incorrect) and 1.0 (perfect).
        """
IQGradablePart = IQPart  # alias


class IQSingleValuedSolution(IQSolution):
    """
    A solution consisting of a single value.
    """
    value = interface.Attribute("The correct value")


class IQMultiValuedSolution(IQSolution):
    """
    A solution consisting of a set of values.
    """
    value = ListOrTuple(title=u"The correct answer selections",
                        description=u"The correct answer as a tuple of items which are a "
                        u"zero-based index into the choices list.",
                        min_length=0,
                        value_type=TextLine(title=u"The value"))


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

    allowed_units = IndexedIterable(title=u"Strings naming unit suffixes",
                                    description=u"""
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
                                    value_type=TextLine(title=u"The unit"))


class IQNumericMathSolution(IQMathSolution, IQSingleValuedSolution):
    """
    A solution whose correct answer is numeric in nature, and
    should be graded according to numeric equivalence.
    """

    value = Float(title=u"The correct numeric answer; really an arbitrary number")


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

    value = _LatexTextLine(title=u"The LaTeX form of the correct answer.",
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

    choices = ListOrTuple(title=u"The choice strings to present to the user.",
                          min_length=1,
                          description=u"""Presentation order may matter, hence the list. But for grading purposes,
                            the order does not matter and simple existence within the set is sufficient.""",
                          value_type=_ContentFragment(title=u"A rendered value"))

IQNonGradableMultipleChoicePart.setTaggedValue('response_type', IQTextResponse)


class IQMultipleChoiceSolution(IQSolution, IQSingleValuedSolution):
    """
    A solution whose correct answer is drawn from a fixed list
    of possibilities. The student is expected to choose from
    the options presented. These will typically be used in isolation as a single part.
    """

    value = interface.Attribute("The correct answer as the zero-based index into the choices list.")


class IQMultipleChoicePart(IQNonGradableMultipleChoicePart, IQPart):

    solutions = IndexedIterable(title=u"The multiple-choice solutions",
                                min_length=0,
                                value_type=Object(IQMultipleChoiceSolution,
                                                  title=u"Multiple choice solution"),
                                required=False)
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

    value = ListOrTuple(title=u"The correct answer selections",
                        description=u"The correct answer as a tuple of items which are a zero-based index into the choices list.",
                        min_length=1,
                        value_type=Int(title=u"The value", min=0))


class IQMultipleChoiceMultipleAnswerPart(IQNonGradableMultipleChoiceMultipleAnswerPart,
                                         IQMultipleChoicePart):

    solutions = IndexedIterable(title=u"The multiple-choice solutions",
                                min_length=0,
                                value_type=Object(IQMultipleChoiceMultipleAnswerSolution,
                                                  title=u"Multiple choice / multiple answer solution"),
                                required=False)


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

    value = Variant((TextLine(title=u"The correct text response", min_length=1),
                     Object(IRegEx, title=u"The regex object")),
                    title=u"The correct regex")


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

    labels = List(title=u"The list of labels",
                  min_length=2,
                  value_type=_ContentFragment(title=u"A label-column value"))

    values = List(title=u"The list of values",
                  min_length=2,
                  value_type=_ContentFragment(title=u"A value-column value"))


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
    value = Dict(title=u"The correct mapping.")


class IQMatchingSolution(IQConnectingSolution):
    pass


class IQOrderingSolution(IQConnectingSolution):
    pass


class IQConnectingPart(IQNonGradableConnectingPart, IQPart):  # BWC
    pass
IQGradableConnectingPart = IQConnectingPart  # alias


class IQMatchingPart(IQNonGradableMatchingPart, IQConnectingPart):

    solutions = IndexedIterable(title=u"The matching solution",
                                min_length=0,
                                value_type=Object(IQMatchingSolution, 
                                                  title=u"Matching solution"),
                                required=False)
IQGradableMatchingPart = IQMatchingPart  # alias


class IQOrderingPart(IQNonGradableOrderingPart, IQConnectingPart):

    solutions = IndexedIterable(title=u"The matching solution",
                                min_length=0,
                                value_type=Object(IQOrderingSolution, 
                                                  title=u"Ordering solution"),
                                required=False)
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


DEFAULT_MIN_SIZE_BYTES = 10485760  # 10 mb
DEFAULT_MAX_SIZE_BYTES = 52428800  # 50 mb


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

    allowed_mime_types = IndexedIterable(title=u"Mime types that are accepted for upload",
                                         min_length=1,
                                         value_type=Text(title=u"An allowed mimetype",
                                                         constraint=rfc2047MimeTypeConstraint))

    allowed_extensions = IndexedIterable(title=u"Extensions like '.doc' that are accepted for upload",
                                         min_length=0,
                                         value_type=Text(title=u"An allowed extension"))

    max_file_size = Int(title=u"Maximum size in bytes for the file",
                        required=False,
                        default=DEFAULT_MIN_SIZE_BYTES)

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


# editable


class IQEditableEvaluation(IQEvaluation):
    """
    Marker interface for all editable objects
    """
IQEditableEvaluation.setTaggedValue('_ext_is_marker_interface', True)
IQEditable = IQEditableEvalutation = IQEditableEvaluation  # alias


# assessment


class IQAssessment(IQEvaluation, IRecordable):
    """
    Marker interface for all assessment objects
    """
IQAssessment.setTaggedValue('_ext_jsonschema', u'')


# question


class IQuestion(IQAssessment, IPublishable, INoPublishLink, IAttributeAnnotatable):
    """
    A question consists of one or more parts (typically one) that require answers.
    It may have prefacing text. It may have other metadata, such as what
    concepts it relates to (e.g., Common Core Standards numbers); such concepts
    will be domain specific.

    Questions are annotatable. Uses of this include things like references
    to where questions appear in question sets or other types of content.
    """

    ntiid = ValidNTIID(title=u"Question NTIID", required=False)

    content = Text(title=u"The content to present to the user, if any.",
                   default=u'')

    parts = IndexedIterable(title=u"The ordered parts of the question.",
                            min_length=1,
                            value_type=Object(IQPart, title=u"A question part"))
IQuestion.setTaggedValue('_ext_jsonschema', u'question')


class IQuestionSet(IQAssessment, ITitledContent, IQEvaluationItemContainer,
                   IAttributeAnnotatable, IRecordableContainer):
    """
    An ordered group of related questions generally intended to be
    completed as a unit (aka, a Quiz or worksheet).

    Question sets are annotatable; Uses of this include things like
    references to where question sets are defined in content or
    which assignments reference them.
    """

    ntiid = ValidNTIID(title=u"Question set NTIID", required=False)

    questions = IndexedIterable(title=u"The ordered questions in the set.",
                                description=u"For convenience, this should also be aliased to `parts`",
                                min_length=0,
                                default=(),
                                value_type=Object(IQuestion, title=u"The questions"))

    def append(item):
        """
        Add the specified :class:`IQuestion` to this set
        """
    add = append

    def pop(index):
        """
        Pop the :class:`IQuestion` at the specified index
        """

    def insert(index, item):
        """
        Insert the specified :class:`IQuestion` item at the specified index
        """
IQuestionSet.setTaggedValue('_ext_jsonschema', u'questionset')


class IQuestionInsertedInContainerEvent(IObjectModifiedEvent):
    """
    Question inserted in container event
    """
    container = interface.Attribute("The Insertion container")
    question = interface.Attribute("The inserted question")
    index = interface.Attribute("The Insertion index")


@interface.implementer(IQuestionInsertedInContainerEvent)
class QuestionInsertedInContainerEvent(ObjectModifiedEvent):

    container = alias('object')

    def __init__(self, container, question=None, index=None):
        super(QuestionInsertedInContainerEvent, self).__init__(container)
        self.index = index
        self.question = question


class IQuestionRemovedFromContainerEvent(IObjectModifiedEvent):
    """
    Question removed from container event
    """
    container = interface.Attribute("The Insertion container")
    question = interface.Attribute("The inserted question")
    index = interface.Attribute("The Insertion index")


@interface.implementer(IQuestionRemovedFromContainerEvent)
class QuestionRemovedFromContainerEvent(ObjectModifiedEvent):

    container = alias('object')

    def __init__(self, container, question=None, index=None):
        super(QuestionRemovedFromContainerEvent, self).__init__(container)
        self.index = index
        self.question = question


class IQAssignmentPart(ITitledContent):
    """
    One portion of an assignment.
    """

    content = Text(title=u"Additional content for the question set in the context of an assignment.",
                   default=u'')

    question_set = Object(IQuestionSet,
                          title=u"The question set to submit with this part")

    auto_grade = Bool(title=u"Should this part be run through the grading machinery?",
                      default=True)
IQAssignmentPart.setTaggedValue('_ext_jsonschema', u'assignmentpart')


class IQSubmittable(IRecordable, ICalendarPublishable, IVersioned):

    available_for_submission_beginning = Datetime(
        title=u"Submissions are accepted no earlier than this.",
        description=u"""When present, this specifies the time instant at which
        submissions of this object may begin to be accepted. If this is absent,
        submissions are always allowed. While this is represented here as an actual
        concrete timestamp, it is expected that in many cases the source representation
        will be relative to something else (a ``timedelta``) and conversion to absolute
        timestamp will be done as needed.""",
        required=False)

    available_for_submission_ending = Datetime(
        title=u"Submissions are accepted no later than this.",
        description=u"""When present, this specifies the last instance at which
        submissions will be accepted. It can be considered the object's "due date."
        As with ``available_for_submission_beginning``,
        this will typically be relative and converted.""",
        required=False)

    no_submit = Bool(title=u"Whether this object accept submissions",
                     default=False)


class IQAssignment(IQAssessment, IQSubmittable, ITitledContent, IAttributeAnnotatable, IReportContext):
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

    ntiid = ValidNTIID(title=u"Assignment NTIID", required=False)

    content = Text(title=u"The content to present to the user, if any.",
                   default=u'')

    category_name = Tag(title=u"Assignments can be grouped into categories.",
                        description=u"""By providing this information, assignments
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
                        default=u'default',
                        required=True)

    parts = IndexedIterable(title=u"The ordered parts of the assignment.",
                            description=u"""Unlike questions, assignments with zero parts are allowed.
                        Because they accept no input, such an assignment is very
                        special and serves as a marker to higher levels of code.
                        """,
                            min_length=0,
                            default=(),
                            value_type=Object(IQAssignmentPart, title=u"An assignment part"))

    is_non_public = Bool(title=u"Whether this assignment should be public or restricted",
                         description=u"""An ill-defined semi-layer violation. Set it to true if
                         this should somehow be non-public and not available to everyone. This
                         is the default. Specific applications will determine what should and should
                         not be public""",
                         default=False)

    title = TextLine(title=u"Assignment title", required=True,
                     min_length=1, max_length=140)

    # A note on handling assignments that have an associated time limit
    # (e.g., you have one hour to complete this assignment once you begin):
    # That information will be encoded as a timedelta on the assignment.
    # The server will accept an "open" request for the assignment and make a
    # note of the time stamp. When submission is attempted, the server
    # will check that the assignment has been opened, and the elapsed time.
    # Depending on the policy and context, submission will either be blocked,
    # or the elapsed time will simply be recorded.

    def iter_question_sets():
        """
        return an iterator with the question sets in this assignment
        """

IQAssignment['title'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQAssignment['title'].setTaggedValue(TAG_REQUIRED_IN_UI, True)
IQAssignment['category_name'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQAssignment['category_name'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQAssignment['is_non_public'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQAssignment['is_non_public'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQAssignment['available_for_submission_ending'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQAssignment['available_for_submission_ending'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQAssignment['available_for_submission_beginning'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQAssignment['available_for_submission_beginning'].setTaggedValue(TAG_REQUIRED_IN_UI, False)

IQAssignment.setTaggedValue('_ext_jsonschema', u'assignment')


class IQTimedAssignment(IQAssignment):

    # Give students at least 59s.
    maximum_time_allowed = Int(title=u"Maximum Time Allowed (Seconds)",
                               description=u"""When present, this specifies the maximum time allowed (in
                               seconds) students have to submit the assignments""",
                               required=True,
                               min=59)

IQTimedAssignment['title'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQTimedAssignment['title'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQTimedAssignment['category_name'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQTimedAssignment['category_name'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQTimedAssignment['is_non_public'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQTimedAssignment['is_non_public'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQTimedAssignment['available_for_submission_ending'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQTimedAssignment['available_for_submission_ending'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQTimedAssignment['available_for_submission_beginning'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQTimedAssignment['available_for_submission_beginning'].setTaggedValue(TAG_REQUIRED_IN_UI, False)


class IQDiscussionAssignment(IQAssignment):
    """
    An assignment without parts or questions that merely contains a pointer to
    a discussion.
    """

    discussion_ntiid = ValidNTIID(title=u"Discussion NTIID", required=False)

    parts = IndexedIterable(title=u"The ordered parts of the assignment.",
                            description=u"Discussion assignments should have no parts.",
                            max_length=0,
                            default=())

IQDiscussionAssignment['title'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQDiscussionAssignment['title'].setTaggedValue(TAG_REQUIRED_IN_UI, True)
IQDiscussionAssignment['category_name'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQDiscussionAssignment['category_name'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQDiscussionAssignment['is_non_public'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQDiscussionAssignment['is_non_public'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQDiscussionAssignment['available_for_submission_ending'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQDiscussionAssignment['available_for_submission_ending'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQDiscussionAssignment['available_for_submission_beginning'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQDiscussionAssignment['available_for_submission_beginning'].setTaggedValue(TAG_REQUIRED_IN_UI, False)


class IQAssessmentContextMixin(interface.Interface):

    def assessments():
        """
        return a [new] list of assessment ids in this context.
        """
    assignments = assessments  # alias for BWC

    def clear():
        """
        clear all policies

        :return true if policies were cleared
        """

    def get(assessment, name, default=None):
        """
        Return the attribute value for the specified assessment
        """

    def set(assessment, name, value):
        """
        Set the attribute value for the specified assessment
        """

    def remove(assessment, name):
        """
        Remove the attribute value for the specified assessment
        """

    def size():
        """
        return the number of assessments
        """

    def __len__():
        """
        return the number of assessments
        """

    def __delitem__(key):
        pass


class IQAssessmentDateContext(IQAssessmentContextMixin):
    """
    An object that can be used as context to adapt an assessment
    date.

    This package provides no implementations of this interface.
    """

    def of(assessment):
        """
        Given an assessment, return an object having the same date
        attributes as the assessment, but interpreted in the context
        of this object. If no changes are required, can return the assessment
        itself.
        """
IQAssignmentDateContext = IQAssessmentDateContext  # alias for BWC


class IQAssessmentPolicies(IQAssessmentContextMixin):

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
IQAssignmentPolicyValidator = IQAssessmentPolicyValidator  # alias for BWC


class IQAssessmentDateContextModified(IObjectModifiedEvent):
    assesment = interface.Attribute("Assesment identifier")


@interface.implementer(IQAssessmentDateContextModified)
class QAssessmentDateContextModified(ObjectModifiedEvent):

    def __init__(self, obj, assesment=None, *descriptions):
        super(QAssessmentDateContextModified, self).__init__(obj, *descriptions)
        self.assesment = assesment


class IQAssessmentPoliciesModified(IObjectModifiedEvent):
    assesment = interface.Attribute("Assesment identifier")
    key = interface.Attribute("Key set")
    value = interface.Attribute("Value set")


@interface.implementer(IQAssessmentPoliciesModified)
class QAssessmentPoliciesModified(ObjectModifiedEvent):

    def __init__(self, obj, assesment=None, key=None, value=None, *descriptions):
        super(QAssessmentPoliciesModified, self).__init__(obj, *descriptions)
        self.key = key
        self.value = value
        self.assesment = assesment


class IUnlockQAssessmentPolicies(IObjectEvent):
    courses = interface.Attribute("Courses set")


@interface.implementer(IUnlockQAssessmentPolicies)
class UnlockQAssessmentPolicies(ObjectEvent):

    assessment = alias('object')

    def __init__(self, obj, courses=None):
        super(UnlockQAssessmentPolicies, self).__init__(obj)
        self.courses = courses or ()


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
            # adapt or return if already present
            result = response_type(response, alternate=None)
            if result is not None:
                response = result
                break
    return response

# Objects having to do with the assessment process itself.
# There is a three part lifecycle: The source object,
# the submission, and finally the assessed value. The three
# parts have similar structure.


class IQBaseSubmission(IContained, IVersioned):
    """
    The root of the tree for submission objects.
    """

    CreatorRecordedEffortDuration = Number(
        title=u"A fractional count of seconds spent creating the submission",
        description=u"""If desired, the creator (i.e., external client) can
        "optionally track the amount of time spent creating the submission and
        "submit it here with the initial submission; after that it is immutable and
        "(currently) unseen. NOTE: Because this is tracked and submitted by the client,
        "it is NOT suitable to use for any actual assessment purposes such as imposing time
        "limits.""",
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

    parts = IndexedIterable(title=u"Ordered submissions, one for each part of the poll.",
                            default=(),
                            description=u"""The length must match the length of the questions. Each object must be
                            adaptable into the proper :class:`IQResponse` object (e.g., a string or dict).""")


class IQuestionSubmission(IQPartsSubmission):
    """
    A student's submission in response to a question.

    These will typically be transient objects.
    """

    questionId = TextLine(title=u"Identifier of the question being responded to.")


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
                                 # List this so we get specific validation for
                                 # it
                                 Object(IQModeledContentResponse),
                                 Object(IQResponse)),
                                variant_raise_when_schema_provided=True,
                                title=u"The response as the student submitted it, or None if they skipped",
                                required=False,
                                default=None)


class IQAssessedPart(IQSubmittedPart):
    """
    The assessed value of a single part.

    """
    # TODO: Matching to question?

    assessedValue = Float(title=u"The relative correctness of the submitted response, from 0.0 (entirely wrong) to 1.0 (perfectly correct)",
                          description=u"A value of None means that it was not possible to assess this part.",
                          min=0.0,
                          max=1.0,
                          default=0.0,
                          required=False)


class IQAssessedQuestion(IContained):
    """
    The assessed value of a student's submission for a single question.

    These will typically be persistent values, echoed back to clients.
    """

    questionId = TextLine(title=u"Identifier of the question being responded to.")
    parts = IndexedIterable(title=u"Ordered assessed values, one for each part of the question.",
                            value_type=Object(IQAssessedPart, title=u"The assessment of a part."))


class IQuestionSetSubmission(IQBaseSubmission):
    """
    A student's submission in response to an entire question set.

    These will generally be transient objects.
    """

    questionSetId = TextLine(title=u"Identifier of the question set being responded to.")
    questions = IndexedIterable(title=u"Submissions, one for each question in the set.",
                                description=u"""Order is not important. Depending on the question set,
                                missing answers may or may not be allowed; the set may refuse to grade, or simply consider them wrong.""",
                                default=(),
                                value_type=Object(IQuestionSubmission,
                                                  title=u"The submission for a particular question."))


class IQAssessedQuestionSet(IContained, IContextAnnotatable):
    """
    The assessed value of a student's submission to an entire question set.

    These will usually be persistent values that are also echoed back to clients.
    """

    questionSetId = TextLine(title=u"Identifier of the question set being responded to.")
    questions = IndexedIterable(title=u"Assessed questions, one for each question in the set.",
                                value_type=Object(IQAssessedQuestion,
                                                  title=u"The assessed value for a particular question."))


class IQAssignmentSubmission(IQBaseSubmission):
    """
    A student's submission in response to an assignment.
    """

    assignmentId = TextLine(title=u"Identifier of the assignment being responded to.")
    parts = IndexedIterable(title=u"Question set submissions, one for each part of the assignment.",
                            description=u"""Order is not significant, each question set will be matched
                            with the corresponding part by ID. However, each part *must* have a
                            submission.""",
                            default=(),
                            value_type=Object(IQuestionSetSubmission,
                                              title=u"The submission for a particular part."))


class IQAssignmentSubmissionPendingAssessment(IQBaseSubmission):
    """
    A submission for an assignment that cannot be completely assessed;
    complete assessment is pending. This is typically the step after
    submission and before completion.
    """

    assignmentId = TextLine(title=u"Identifier of the assignment being responded to.")
    parts = IndexedIterable(title=u"Either an assessed question set, or the original submission",
                            value_type=Variant(
                                (Object(IQAssessedQuestionSet),
                                 Object(IQuestionSetSubmission))))


class IPlaceholderAssignmentSubmission(IQAssignmentSubmission):
    """
    Marker interface for submissions created as placeholders.
    """


class IQAssessmentItemContainer(IEnumerableMapping):
    """
    Something that is an unordered bag of assessment items (such as
    questions, question sets, and assignments).

    This package provides no implementation of this interface. (But
    something like the content library package may be adaptable to this,
    typically with annotations).
    """

    def append(item):
        """
        Add an item to this container
        """

    def extend(items):
        """
        Add the specified items to this container
        """

    def assessments():
        """
        return an iterable with all assessmentsi this container
        """

    def pop(k, *args):
        """
        remove specified key and return the corresponding value
        *args may contain a single default value, or may not be supplied.
        If key is not found, default is returned if given, otherwise
        KeyError is raised
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


class IQFillInTheBlankShortAnswerSolution(IQSolution):

    value = Dict(key_type=TextLine(title=u"input name/id"),
                 value_type=Variant((TextLine(title=u"The pattern"),
                                     Object(IRegEx, title=u"The regex object")),
                                    title=u"The correct regex"),
                 title=u"The correct answer regexes",
                 description=u"The correct word id map.",
                 min_length=1)

IQFillInTheBlankShortAnswerSolution.setTaggedValue('response_type', IQDictResponse)


class IQFillInTheBlankShortAnswerPart(IQNonGradableFillInTheBlankShortAnswerPart,
                                      IQFillInTheBlankPart):
    """
    Marker interface for a Fill-in-the-blank short answer question part.
    """

    solutions = IndexedIterable(title=u"The solutions",
                                min_length=0,
                                required=False,
                                value_type=Object(IQFillInTheBlankShortAnswerSolution,
                                                  title=u"the solution"))


class IQFillInTheBlankWithWordBankGrader(IQPartGrader):
    pass


class IQFillInTheBlankWithWordBankSolution(IQSolution):

    value = Dict(key_type=TextLine(title=u"input name/id"),
                 value_type=Variant((TextLine(title=u"word id answer"),
                                     ListOrTuple(TextLine(title=u"word id answer"))),
                                    title=u"The word ids"),
                 title=u"The correct answer selections",
                 description=u"The correct word id map.",
                 min_length=1)

IQFillInTheBlankWithWordBankSolution.setTaggedValue('response_type', IQDictResponse)


# fill-in-the-blank with word bank part


class IWordEntry(interface.Interface):
    wid = TextLine(title=u"word identifier")
    word = TextLine(title=u"the word")
    lang = TextLine(title=u"language identifier", default=u"en", required=False)
    content = _ContentFragment(title=u"The input to present to the user.",
                               required=False)


class IWordBank(IIterable, IReadMapping):

    entries = ListOrTuple(title=u"The word entries",
                          value_type=Object(IWordEntry, title=u"The word"),
                          min_length=1)

    unique = Bool(title=u"A word can be used once in a question/part",
                  default=True, required=False)


class IQNonGradableFillInTheBlankWithWordBankPart(IQFillInTheBlankPart):
    """
    Marker interface for a Fill-in-the-blank with word bank question part.
    If the word bank is not specified it would the one from the parent question
    """

    wordbank = Object(IWordBank, required=False,
                      title=u"The wordbank to present to the user.")

    input = _HTMLContentFragment(title=u"The input to present to the user.")


class IQFillInTheBlankWithWordBankPart(IQNonGradableFillInTheBlankWithWordBankPart,
                                       IQFillInTheBlankPart):

    solutions = IndexedIterable(title=u"The solutions",
                                min_length=0,
                                required=False,
                                value_type=Object(IQFillInTheBlankWithWordBankSolution,
                                                  title=u"the solution"))


class IQFillInTheBlankWithWordBankQuestion(IQuestion):
    """
    Marker interface for a Fill-in-the-blank with word bank question.

    The word bank for the question may be used by any question parts
    """
    wordbank = Object(IWordBank, required=False)

    parts = IndexedIterable(title=u"The ordered parts of the question.",
                            min_length=1,
                            value_type=Object(IQFillInTheBlankWithWordBankPart,
                                              title=u"A question part"))


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

DISCLOSURE_STATES = (DISCLOSURE_NEVER,
                     DISCLOSURE_ALWAYS,
                     DISCLOSURE_TERMINATION)
DISCLOSURE_VOCABULARY = vocabulary.SimpleVocabulary(
    [vocabulary.SimpleTerm(_x) for _x in DISCLOSURE_STATES])


class IQInquiry(IQSubmittable, IQEvaluation, IAttributeAnnotatable, IReportContext):

    ntiid = ValidNTIID(title=u"Object NTIID", required=False)

    disclosure = Choice(vocabulary=DISCLOSURE_VOCABULARY, title=u'Disclosure policy',
                        required=True, default=DISCLOSURE_TERMINATION)

    closed = Bool(title=u"Close flag", required=False, default=False)
    closed.setTaggedValue('_ext_excluded_out', True)

    no_submit = Bool(title=u"Whether this object accept submissions",
                     default=False, required=False)
    no_submit.setTaggedValue('_ext_excluded_out', True)

    is_non_public = Bool(title=u"Whether this inquiry should be public or restricted",
                         default=False)


class IQPoll(IQInquiry, IFiniteSequence):
    """
    A poll question consists of one or more parts (typically one).
    It may have prefacing text. It may have other metadata, such as what
    concepts it relates to (e.g., Common Core Standards numbers); such concepts
    will be domain specific.

    Polls are annotatable. Uses of this include things like references
    to where questions appear in question sets or other types of content.
    """

    content = Text(title=u"The content to present to the user, if any.",
                   default=u'', required=False)

    parts = IndexedIterable(title=u"The ordered parts of the question.",
                            min_length=1,
                            value_type=Object(IPollable, title=u"A pollable question part"))


IQPoll['closed'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQPoll['closed'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQPoll['disclosure'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQPoll['disclosure'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQPoll['available_for_submission_ending'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQPoll['available_for_submission_ending'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQPoll['available_for_submission_beginning'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQPoll['available_for_submission_beginning'].setTaggedValue(TAG_REQUIRED_IN_UI, False)

IQPoll.setTaggedValue('_ext_jsonschema', u'poll')


class IQSurvey(IQInquiry, ITitledContent, IQEvaluationItemContainer, IFiniteSequence):
    """
    An ordered group of poll questions.

    Surveys sets are annotatable.
    """

    questions = IndexedIterable(title=u"The ordered polls in the set.",
                                min_length=0,
                                default=(),
                                value_type=Object(IQPoll, title=u"The poll questions"))


IQSurvey['title'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQSurvey['title'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQSurvey['closed'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQSurvey['closed'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQSurvey['disclosure'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQSurvey['disclosure'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQSurvey['available_for_submission_ending'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQSurvey['available_for_submission_ending'].setTaggedValue(TAG_REQUIRED_IN_UI, False)
IQSurvey['available_for_submission_beginning'].setTaggedValue(TAG_HIDDEN_IN_UI, False)
IQSurvey['available_for_submission_beginning'].setTaggedValue(TAG_REQUIRED_IN_UI, False)

IQSurvey.setTaggedValue('_ext_jsonschema', u'survey')


class IQInquirySubmission(IQPartsSubmission):
    inquiryId = interface.Attribute("Identifier of the inquiry being responded to.")
    inquiryId.setTaggedValue('_ext_excluded_out', True)


class IQPollSubmission(IQInquirySubmission):
    """
    A submission in response to a poll.

    These will typically be transient objects.
    """

    pollId = TextLine(title=u"Identifier of the poll being responded to.")


class IQSurveySubmission(IQInquirySubmission, IContextAnnotatable, IWriteMapping):
    """
    A submission in response to a survey
    """

    surveyId = TextLine(title=u"Identifier of the survey being responded to.")
    questions = IndexedIterable(title=u"Submissions, one for each poll in the survey.",
                                default=(),
                                value_type=Object(IQPollSubmission,
                                                  title=u"The submission for a particular poll."))


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

    Results = Dict(title=u"The response results",
                   key_type=Tuple(title=u"The response tuples",
                                  min_length=1,
                                  value_type=Tuple(title=u"The choices")),
                   value_type=Number(title=u"The aggregated value"),
                   readonly=True)


class IQAggregatedMatchingPart(IQAggregatedConnectingPart):
    pass


class IQAggregatedOrderingPart(IQAggregatedConnectingPart):
    pass


class IQAggregatedMultipleChoicePart(IQAggregatedPart):

    Results = Dict(title=u"The response results",
                   key_type=Int(title=u"The choice index"),
                   value_type=Number(title=u"The aggregated value"),
                   readonly=True)


class IQAggregatedMultipleChoiceMultipleAnswerPart(IQAggregatedMultipleChoicePart):

    Results = Dict(title=u"The response results",
                   key_type=Tuple(title=u"The response tuple",
                                  min_length=1,
                                  value_type=Int(title=u"The choice indices")),
                   value_type=Number(title=u"The aggregated value"),
                   readonly=True)


class IQAggregatedFreeResponsePart(IQAggregatedPart):

    Results = Dict(title=u"The response results",
                   key_type=TextLine(title=u"the value"),
                   value_type=Number(title=u"The aggregated value"),
                   readonly=True)


class IQAggregatedModeledContentPart(IQAggregatedPart):

    Results = List(title=u"The response results",
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

    pollId = TextLine(title=u"Identifier of the poll being aggregated.")
    parts = IndexedIterable(title=u"Part aggregations.",
                            default=(),
                            value_type=Object(IQAggregatedPart,
                                              title=u"The aggregated part."))


class IQAggregatedSurvey(IQAggregatedInquiry, IIterable, IWriteMapping):
    """
    Aggregation for a survey
    """

    surveyId = TextLine(title=u"Identifier of the survey being aggregated.")
    questions = IndexedIterable(title=u"Poll aggregations.",
                                default=(),
                                value_type=Object(IQAggregatedPoll,
                                                  title=u"The aggregated poll."))


# misc


class IQEvaluationContainerIdGetter(interface.Interface):
    """
    A interface for a utility to get the containerId of an assessment
    """

    def __call__(item):
        pass
IQAssessmentContainerIdGetter = IQEvaluationContainerIdGetter  # BWC


class IQEvaluationJsonSchemaMaker(IObjectJsonSchemaMaker):
    """
    Marker interface for an evaluation JSON Schema maker utility
    """

    def make_schema(schema=IQEvaluation, user=None):
        pass
IQAssessmentJsonSchemaMaker = IQEvaluationJsonSchemaMaker


#: Question moved recorder transaction type.
TRX_QUESTION_MOVE_TYPE = u'questionmoved'


class IQuestionMovedEvent(IObjectEvent):
    pass


@interface.implementer(IQuestionMovedEvent)
class QuestionMovedEvent(ObjectEvent):

    question = alias('object')

    def __init__(self, obj, principal=None, index=None, old_parent_ntiid=None):
        super(QuestionMovedEvent, self).__init__(obj)
        self.index = index
        self.principal = principal
        self.old_parent_ntiid = old_parent_ntiid
