#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.interface.interfaces import IMethod

from nti.assessment.interfaces import IQPart
from nti.assessment.interfaces import IQPoll
from nti.assessment.interfaces import IQSurvey
from nti.assessment.interfaces import IQuestion
from nti.assessment.interfaces import IQuestionSet
from nti.assessment.interfaces import IQAssignment
from nti.assessment.interfaces import IQNonGradablePart
from nti.assessment.interfaces import IQTimedAssignment

from nti.assessment.randomized.interfaces import IQuestionBank
from nti.assessment.randomized.interfaces import IRandomizedQuestionSet

from nti.schema.jsonschema import TAG_HIDDEN_IN_UI

EVALUATION_INTERFACES = ASSESSMENT_INTERFACES = ( # order matters
        IQPoll, 
        IQuestion,
        IQSurvey, 
        IQuestionBank,
        IRandomizedQuestionSet,
        IQuestionSet,
        IQTimedAssignment, 
        IQAssignment
)

def _set_ifaces():
    for iSchema in ASSESSMENT_INTERFACES:
        for k, v in iSchema.namesAndDescriptions(all=True):
            if IMethod.providedBy(v) or v.queryTaggedValue(TAG_HIDDEN_IN_UI) is not None:
                continue
            iSchema[k].setTaggedValue(TAG_HIDDEN_IN_UI, True)
_set_ifaces()
del _set_ifaces
