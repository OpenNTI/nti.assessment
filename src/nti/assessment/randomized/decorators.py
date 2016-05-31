#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.assessment.randomized.interfaces import IQRandomizedPart

from nti.externalization.interfaces import IExternalMappingDecorator

@component.adapter(IQRandomizedPart)
@interface.implementer(IExternalMappingDecorator)
class _RandomizedPartDecorator(object):

	def __init__(self, part):
		self.part = part

	def decorateExternalMapping(self, original, external):
		external['randomized'] = True
		return external
