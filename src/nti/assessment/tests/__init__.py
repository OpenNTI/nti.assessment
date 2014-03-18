#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_key
from hamcrest import has_entry
from hamcrest import assert_that
from hamcrest.core.base_matcher import BaseMatcher

import nti.testing.base
from nti.testing.layers import find_test
from nti.testing.layers import GCLayerMixin
from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin

import zope.testing.cleanup

from nti.dataserver.tests.mock_dataserver import DSInjectorMixin

class GradeMatcher(BaseMatcher):
	def __init__( self, value, response ):
		super(GradeMatcher,self).__init__()
		self.value = value
		self.response = response

	def _matches( self, solution ):
		return solution.grade( self.response ) == self.value

	def describe_to( self, description ):
		description.append_text( 'solution that grades ').append_text( str(self.response) ).append_text( ' as ' ).append_text( str(self.value) )

	def describe_mismatch( self, item, mismatch_description ):
		mismatch_description.append_text( 'solution ' ).append_text( str(type(item) ) ).append_text( ' ' ).append_text( str(item) )
		if getattr( item, 'allowed_units', () ):
			mismatch_description.append_text( " units " + str( item.allowed_units ) )

		mismatch_description.append_text( ' graded ' + str(self.response) + ' as ' + str( not self.value ) )

	def __repr__( self ):
		return 'solution that grades as ' + str(self.value)

def grades_correct( response ):
	return GradeMatcher(True, response)
grades_right = grades_correct

def grades_wrong( response ):
	return GradeMatcher(False, response )

class SharedConfiguringTestLayer(ZopeComponentLayer,
								 GCLayerMixin,
								 ConfiguringLayerMixin,
								 DSInjectorMixin):

	set_up_packages = ('nti.dataserver', 'nti.assessment',)

	@classmethod
	def setUp(cls):
		cls.setUpPackages()

	@classmethod
	def tearDown(cls):
		cls.tearDownPackages()
		zope.testing.cleanup.cleanUp()

	@classmethod
	def testSetUp(cls, test=None):
		cls.setUpTestDS(test)

	@classmethod
	def testTearDown(cls):
		pass
