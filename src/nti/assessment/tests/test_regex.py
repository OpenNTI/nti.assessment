#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import equal_to
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import has_property

from nti.testing.matchers import verifiably_provides

from nti.assessment.interfaces import IRegEx

from nti.assessment.regex import RegEx

from nti.contentfragments.interfaces import UnicodeContentFragment

from nti.assessment.tests import AssessmentTestCase

from nti.externalization.tests import externalizes


class TestRegex(AssessmentTestCase):

    def test_regex(self):
        rex = RegEx(pattern=u'bankai',
                    solution=UnicodeContentFragment(u'bankai'))

        assert_that(rex, verifiably_provides(IRegEx))
        assert_that(rex, has_property('pattern', 'bankai'))
        assert_that(rex, has_property('solution', 'bankai'))
        assert_that(rex, externalizes(has_entries('Class', 'RegEx',
                                                  'pattern', 'bankai',
                                                  'solution', 'bankai')))

        assert_that(hash(rex), is_(8894945980207509453))

        arex = IRegEx(u'^1\$')
        assert_that(arex, has_property('pattern', '^1\$'))

        lst = [u'bankai', u'bankai']
        arex = IRegEx(lst)
        assert_that(rex, is_(equal_to(arex)))

        tpl = (u'bankai', u'bankai')
        arex = IRegEx(tpl)
        assert_that(rex, is_(equal_to(arex)))
