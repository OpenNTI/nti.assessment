#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""


$Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

#disable: accessing protected members, too many methods
#pylint: disable=W0212,R0904

from .. import response

from hamcrest import assert_that
from hamcrest import is_
from hamcrest import is_not as does_not
from hamcrest import not_none
from hamcrest import none
from hamcrest import has_entry
from hamcrest import has_property
from hamcrest import has_key
from hamcrest import all_of

from nti.externalization import internalization

from nti.testing import base
#from nti.testing import matchers
from nti.externalization.tests import externalizes

# nose module-level setup
setUpModule = lambda: base.module_setup( set_up_packages=(__name__,) )
tearDownModule = base.module_teardown

GIF_DATAURL = b'data:image/gif;base64,R0lGODlhCwALAIAAAAAA3pn/ZiH5BAEAAAEALAAAAAALAAsAAAIUhA+hkcuO4lmNVindo7qyrIXiGBYAOw=='


def test_file_upload():

	ext_obj = {
		'MimeType': 'application/vnd.nextthought.assessment.uploadedfile',
		'value': GIF_DATAURL,
		'filename': r'c:\dir\file.gif'
	}

	assert_that( internalization.find_factory_for( ext_obj ),
				 is_( not_none() ) )

	internal = internalization.find_factory_for( ext_obj )()
	internalization.update_from_external_object( internal,
												 ext_obj,
												 require_updater=True )

	# value changed to URI
	assert_that( ext_obj, does_not( has_key( 'value' ) ) )
	assert_that( ext_obj, has_key( 'url' ) )

	# We produced an image file, not a plain file
	assert_that( internal.getImageSize(), is_( (11,11) ) )
	# with the right content time and filename
	assert_that( internal, has_property( 'mimeType', 'image/gif' ) )
	assert_that( internal, has_property( 'filename', 'file.gif' ) )

	assert_that( internal, externalizes( all_of( has_key( 'FileMimeType' ),
												 has_key( 'filename' ),
												 has_entry( 'url', none() )) ) )
	# But we have no URL because we're not in a connection anywhere

def test_modeled_response_uploade():

	ext_obj = {
		'MimeType': 'application/vnd.nextthought.assessment.modeledcontentresponse',
		'value': ['a part'],
	}

	assert_that( internalization.find_factory_for( ext_obj ),
				 is_( not_none() ) )

	internal = internalization.find_factory_for( ext_obj )()
	internalization.update_from_external_object( internal,
												 ext_obj,
												 require_updater=True )

	assert_that( internal, has_property('value', is_(('a part',))))
