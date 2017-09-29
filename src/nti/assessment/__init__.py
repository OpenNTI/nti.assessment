#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.interface.interfaces import IMethod

#: Evaluation NTIID type
from nti.assessment.interfaces import NTIID_TYPE as NAQ

#: Part NTIID type
from nti.assessment.interfaces import PART_NTIID_TYPE as PART_NAQ

from nti.assessment.interfaces import IQPart
from nti.assessment.interfaces import IQPoll
from nti.assessment.interfaces import IQSurvey
from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQuestionSet
from nti.assessment.interfaces import IQAssignment
from nti.assessment.interfaces import IQNonGradablePart
from nti.assessment.interfaces import IQTimedAssignment
from nti.assessment.interfaces import IQDiscussionAssignment

from nti.assessment.randomized.interfaces import IQuestionBank

from nti.schema.jsonschema import TAG_HIDDEN_IN_UI

#: Fields attribute
FIELDS = u'Fields'

#: Accepts attribute
ACCEPTS = u'Accepts'

EVALUATION_INTERFACES = ASSESSMENT_INTERFACES = (  # order matters
    IQPoll,
    IQuestion,
    IQSurvey,
    IQuestionBank,
    IQuestionSet,
    IQDiscussionAssignment,
    IQTimedAssignment,
    IQAssignment
)


def _set_ifaces():
    for iSchema in ASSESSMENT_INTERFACES:
        for k, v in iSchema.namesAndDescriptions(all=True):
            if     IMethod.providedBy(v) \
                or v.queryTaggedValue(TAG_HIDDEN_IN_UI) is not None:
                continue
            iSchema[k].setTaggedValue(TAG_HIDDEN_IN_UI, True)

_set_ifaces()
del _set_ifaces

from nti.assessment._patch import patch
patch()
del patch
