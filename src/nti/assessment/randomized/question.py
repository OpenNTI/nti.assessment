#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.externalization.externalization import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from .interfaces import IQuestionBank
from .interfaces import IQuestionIndexRange
from .interfaces import IRandomizedQuestionSet

from ..question import QQuestionSet

@interface.implementer(IRandomizedQuestionSet)
class QRandomizedQuestionSet(QQuestionSet):
	createDirectFieldProperties(IRandomizedQuestionSet)
	
	__external_class_name__ = "QQuestionSet"
	mimeType = mime_type = 'application/vnd.nextthought.narandomizedquestionset'


@interface.implementer(IQuestionBank)
@EqHash('draw', include_super=True)
class QQuestionBank(QQuestionSet):
	createDirectFieldProperties(IQuestionBank)
	
	__external_class_name__ = "QQuestionSet"
	mimeType = mime_type = 'application/vnd.nextthought.naquestionbank'

@interface.implementer(IQuestionIndexRange)
@WithRepr
@EqHash('start', 'end')
class QQuestionIndexRange(SchemaConfigured):
	createDirectFieldProperties(IQuestionIndexRange)

	__external_class_name__ = "QQuestionIndexRange"
	mimeType = mime_type = 'application/vnd.nextthought.naqindexrange'
	
@interface.implementer(IQuestionIndexRange)
def _range_adapter(sequence):
	result = QQuestionIndexRange(start=int(sequence[0]), end=int(sequence[1]))
	return result