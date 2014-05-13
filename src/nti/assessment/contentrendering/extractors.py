#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Book extractors

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import six
import codecs
import simplejson as json  # Needed for sort_keys, ensure_ascii

from zope import component
from zope import interface

from plasTeX.Renderers import render_children

from nti.contentrendering import interfaces as crd_interfaces

from nti.externalization import internalization
from nti.externalization.externalization import toExternalObject

from .interfaces import IAssessmentExtractor
from .interfaces import ILessonQuestionSetExtractor

@interface.implementer(IAssessmentExtractor)
@component.adapter(crd_interfaces.IRenderedBook)
class _AssessmentExtractor(object):
	"""
	"Transforms" a rendered book by extracting assessment information into a separate file
	called ``assessment_index.json.`` This file describes a dictionary with the following
	structure::

		Items => { # Keyed by NTIID of the file
			NTIID => string # This level is about an NTIID section
			filename => string # The relative containing file for this NTIID
			AssessmentItems => { # Keyed by NTIID of the question
				NTIID => string # The NTIID of the question
				... # All the rest of the keys of the question object
			}
			Items => { # Keyed by NTIIDs of child sections; recurses
				# As containing, except 'filename' will be null/None
			}
		}

	"""

	def __init__(self, book=None):
		pass

	def transform(self, book):
		index = {'Items': {}}
		self._build_index(book.document.getElementsByTagName('document')[0], index['Items'])
		index['href'] = index.get('href', 'index.html')
		target = os.path.join(book.contentLocation, 'assessment_index.json')
		logger.info("extracting assessments to %s" , target)
		with codecs.open(target, 'w', encoding='utf-8') as fp:
			# sort_keys for repeatability. Do force ensure_ascii because even though
			# we're using codes to  encode automatically, the reader might not decode
			json.dump(index, fp, indent='\t', sort_keys=True, ensure_ascii=True)
		return index

	def _build_index(self, element, index):
		"""
		Recurse through the element adding assessment objects to the index,
		keyed off of NTIIDs.

		:param dict index: The containing index node. Typically, this will be
			an ``Items`` dictionary in a containing index.
		"""
		if self._is_uninteresting(element):
			# It's important to identify uninteresting nodes because
			# some uninteresting nodes that would never make it into the TOC or otherwise be noticed
			# actually can present with hard-coded duplicate NTIIDs, which would
			# cause us to fail.
			return

		ntiid = getattr(element, 'ntiid', None)
		if not ntiid:
			# If we hit something without an ntiid, it's not a section-level
			# element, it's a paragraph or something like it. Thus we collapse into
			# the parent. Obviously, we'll only look for AssessmentObjects inside of here
			element_index = index
		else:
			assert ntiid not in index, ("NTIIDs must be unique", ntiid, index.keys())
			element_index = index[ntiid] = {}

			element_index['NTIID'] = ntiid
			element_index['filename'] = getattr(element, 'filename', None)
			if not element_index['filename'] and getattr(element, 'filenameoverride', None):
				# FIXME: XXX: We are assuming the filename extension. Why aren't we finding
				# these at filename? See EclipseHelp.zpts for comparison
				element_index['filename'] = getattr(element, 'filenameoverride') + '.html'
			element_index['href'] = getattr(element, 'url', element_index['filename'])

		__traceback_info__ = element_index
		assessment_objects = element_index.setdefault('AssessmentItems', {})

		for child in element.childNodes:
			ass_obj = getattr(child, 'assessment_object', None)
			if callable(ass_obj):
				int_obj = ass_obj()
				self._ensure_roundtrips(int_obj, provenance=child)  # Verify that we can round-trip this object
				assessment_objects[child.ntiid] = toExternalObject(int_obj)
				# assessment_objects are leafs, never have children to worry about
			elif child.hasChildNodes():  # Recurse for children if needed
				if getattr(child, 'ntiid', None):
					# we have a child with an NTIID; make sure we have a container for it
					containing_index = element_index.setdefault('Items', {})
				else:
					# an unnamed thing; wrap it up with us; should only have AssessmentItems
					containing_index = element_index
				self._build_index(child, containing_index)

	def _ensure_roundtrips(self, assm_obj, provenance=None):
		ext_obj = toExternalObject(assm_obj)  # No need to go into its children, like parts.
		__traceback_info__ = provenance, assm_obj, ext_obj
		raw_int_obj = type(assm_obj)()  # Use the class of the object returned as a factory.
		internalization.update_from_external_object(raw_int_obj, ext_obj, require_updater=True, notify=False)

		# Also be sure factories can be found
		factory = internalization.find_factory_for(toExternalObject(assm_obj))
		assert factory is not None
		# The ext_obj was mutated by the internalization process, so we need to externalize
		# again. Or run a deep copy (?)

	def _is_uninteresting(self, element):
		"""
		Uninteresting elements do not get an entry in the index. These are
		elements that have no children and no assessment items of their own.
		"""

		cache_attr = '@assessment_extractor_uninteresting'
		if getattr(element, cache_attr, None) is not None:
			return getattr(element, cache_attr)

		boring = False
		if callable(getattr(element, 'assessment_object', None)):
			boring = False
		elif not element.hasChildNodes():
			boring = True
		elif all((self._is_uninteresting(x) for x in element.childNodes)):
			boring = True

		try:
			setattr(element, cache_attr, boring)
		except AttributeError:
			pass

		return boring

@interface.implementer(ILessonQuestionSetExtractor)
@component.adapter(crd_interfaces.IRenderedBook)
class _LessonQuestionSetExtractor(object):

	def __init__(self, book=None):
		pass

	def transform( self, book ):
		questionset_els = book.document.getElementsByTagName( 'naquestionset' )
		assignment_els = book.document.getElementsByTagName( 'naassignment' )
		dom = book.toc.dom
		if questionset_els:
			topic_map = self._get_topic_map(dom)
			self._process_questionsets(dom, questionset_els, topic_map)
			self._process_assignments(dom, assignment_els, topic_map)
			book.toc.save()

	def _get_topic_map(self, dom):
		result = {}
		for topic_el in dom.getElementsByTagName('topic'):
			ntiid = topic_el.getAttribute('ntiid')
			if ntiid:
				result[ntiid] = topic_el
		return result

	def _process_questionsets(self, dom, els, topic_map):
		for el in els:
			if not el.parentNode:
				continue

			# Discover the nearest topic in the toc that is a 'course' node
			parent_el = el.parentNode
			lesson_el = None
			if hasattr(parent_el, 'ntiid') and parent_el.tagName.startswith('course'):
				lesson_el = topic_map.get(parent_el.ntiid)
			while lesson_el is None and parent_el.parentNode is not None:
				parent_el = parent_el.parentNode
				if hasattr(parent_el, 'ntiid') and parent_el.tagName.startswith('course'):
					lesson_el = topic_map.get(parent_el.ntiid)

			# SAJ: Hack to prevent question set sections from appearing on
			# old style course overviews
			title_el = el.parentNode
			while (not hasattr(title_el, 'title')):
				title_el = title_el.parentNode

			# If the title_el is a topic in the ToC of a course, suppress it.
			if dom.childNodes[0].getAttribute('isCourse') == u'true' and title_el.ntiid in topic_map.keys():
				topic_map[title_el.ntiid].setAttribute('suppressed', 'true')

			title = el.title
			if not isinstance(title, six.string_types):
				label = unicode(''.join(render_children(el.renderer, el.title)))
			else:
				label = title

			toc_el = dom.createElement('object')
			toc_el.setAttribute('label', label)
			toc_el.setAttribute('mimeType', el.mimeType)
			toc_el.setAttribute('target-ntiid', el.ntiid)
			toc_el.setAttribute('question-count', el.question_count)
			if lesson_el:
				lesson_el.appendChild(toc_el)
				lesson_el.appendChild(dom.createTextNode(u'\n'))

	# SAJ: This method is a HACK to mark the parent topic of an assignment as 'suppressed'.
	# In practice, this is only needed for 'no_submit' assignments since they have no
	# associated question set to otherwise trigger the marking. This should move into its
	# own extractor, but for now it is here.
	def _process_assignments(self, dom, els, topic_map):
		for el in els:
			if not el.parentNode:
				continue

			category = el.attributes.get('options', {}).get('category')
			if category != u'no_submit':
				continue

			# Discover the nearest topic in the toc that is a 'course' node
			lesson_el = None
			parent_el = el.parentNode
			if hasattr(parent_el, 'ntiid') and parent_el.tagName.startswith('course'):
				lesson_el = topic_map.get(parent_el.ntiid)

			while lesson_el is None and parent_el.parentNode is not None:
				parent_el = parent_el.parentNode
				if hasattr(parent_el, 'ntiid') and parent_el.tagName.startswith('course'):
					lesson_el = topic_map.get(parent_el.ntiid)

			# SAJ: Hack to prevent no_submit assignment sections from appearing on
			# old style course overviews
			title_el = el.parentNode
			while (not hasattr(title_el, 'title')):
				title_el = title_el.parentNode

			# If the title_el is a topic in the ToC of a course, suppress it.
			if dom.childNodes[0].getAttribute('isCourse') == u'true' and title_el.ntiid in topic_map.keys():
				topic_map[title_el.ntiid].setAttribute('suppressed', 'true')

			mimeType = 'application/vnd.nextthought.nanosubmitassignment'

			toc_el = dom.createElement('object')
			toc_el.setAttribute('label', el.title)
			toc_el.setAttribute('mimeType', mimeType)
			toc_el.setAttribute('target-ntiid', el.ntiid)
			if lesson_el:
				lesson_el.appendChild(toc_el)
				lesson_el.appendChild(dom.createTextNode(u'\n'))
