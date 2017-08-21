#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import not_none
from hamcrest import has_entry
from hamcrest import assert_that

from nti.testing.matchers import verifiably_provides

from nti.assessment import interfaces

from nti.externalization import internalization

from nti.externalization.externalization import toExternalObject

from nti.assessment.tests import AssessmentTestCase

from nti.externalization.tests import externalizes


class TestTextHint(AssessmentTestCase):

    def test_externalizes(self):
        hint = interfaces.IQTextHint("The hint")
        assert_that(hint, verifiably_provides(interfaces.IQTextHint))
        assert_that(hint, externalizes(has_entry('Class', 'TextHint')))
        assert_that(internalization.find_factory_for(toExternalObject(hint)),
                    is_(not_none()))

    def test_eq(self):
        hint1 = interfaces.IQTextHint("The hint")
        hint11 = interfaces.IQTextHint("The hint")
        hint2 = interfaces.IQTextHint("The hint2")

        assert_that(hint1, is_(hint11))
        assert_that(hint1, is_(hint11))
        assert_that(hint1, is_not(hint2))

        # Hit the ne operator specifically
        assert hint1 != hint2
