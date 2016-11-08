#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import equal_to
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import has_property

from nti.assessment.regex import RegEx
from nti.assessment import interfaces as asm_interfaces

from nti.contentfragments import interfaces as frag_interfaces

from nti.externalization.tests import externalizes

from nti.testing.matchers import verifiably_provides

from nti.assessment.tests import AssessmentTestCase

class TestRegex(AssessmentTestCase):

	def test_regex(self):
		rex = RegEx(pattern='bankai', solution=frag_interfaces.UnicodeContentFragment('bankai'))
		assert_that(rex, verifiably_provides(asm_interfaces.IRegEx))
		assert_that(rex, has_property('pattern', 'bankai'))
		assert_that(rex, has_property('solution', 'bankai'))
		assert_that(rex, externalizes(has_entries('Class', 'RegEx',
												 'pattern', 'bankai',
												 'solution', 'bankai')))

		assert_that(hash(rex), is_(8894945980207509453))

		arex = asm_interfaces.IRegEx('^1\$')
		assert_that(arex, has_property('pattern', '^1\$'))

		lst = ['bankai', 'bankai']
		arex = asm_interfaces.IRegEx(lst)
		assert_that(rex, is_(equal_to(arex)))

		tpl = ('bankai', 'bankai')
		arex = asm_interfaces.IRegEx(tpl)
		assert_that(rex, is_(equal_to(arex)))
