#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from zope.dottedname import resolve as dottedname

from nti.assessment.tests import AssessmentTestCase


class TestInterfaces(AssessmentTestCase):

    def test_import_interfaces(self):
        dottedname.resolve('nti.assessment.interfaces')
