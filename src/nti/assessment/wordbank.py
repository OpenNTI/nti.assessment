#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
from functools import total_ordering

from zope import interface

from zope.container.contained import Contained

from persistent import Persistent

from nti.assessment.interfaces import IWordBank
from nti.assessment.interfaces import IWordEntry

from nti.common.maps import CaseInsensitiveDict

from nti.common.property import CachedProperty

from nti.common.string import to_unicode

from nti.contentfragments.interfaces import HTMLContentFragment

from nti.externalization.representation import WithRepr

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties

def safe_encode(word, encoding="UTF-8"):
	word = str(word) if not isinstance(word, six.string_types) else word
	try:
		word = word.encode(encoding)
	except Exception:
		word = repr(word)
	return word

@WithRepr
@EqHash("wid")
@total_ordering
@interface.implementer(IWordEntry)
class WordEntry(SchemaConfigured, Persistent, Contained):
	createDirectFieldProperties(IWordEntry)

	__external_can_create__ = True
	mime_type = mimeType = 'application/vnd.nextthought.naqwordentry'

	wid = None
	word = None
	lang = 'en'

	def __init__(self, *args, **kwargs):
		Persistent.__init__(self)
		SchemaConfigured.__init__(self, *args, **kwargs)

	def __lt__(self, other):
		try:
			return (self.word.lower(), self.lang) < (other.word.lower(), other.self.lang)
		except AttributeError:
			return NotImplemented

	def __gt__(self, other):
		try:
			return  (self.word.lower(), self.lang) > (other.word.lower(), other.self.lang)
		except AttributeError:
			return NotImplemented

@WithRepr
@EqHash("ids", "unique")
@interface.implementer(IWordBank)
class WordBank(SchemaConfigured, Persistent, Contained):
	createDirectFieldProperties(IWordBank)

	__external_can_create__ = True
	mime_type = mimeType = 'application/vnd.nextthought.naqwordbank'

	entries = ()
	unique = None

	def __init__(self, *args, **kwargs):
		Persistent.__init__(self)
		SchemaConfigured.__init__(self, *args, **kwargs)

	@CachedProperty('entries')
	def words(self):
		return frozenset({x.word for x in self.entries})

	@CachedProperty('entries')
	def ids(self):
		return frozenset({x.wid for x in self.entries})

	def sorted(self):
		return sorted(self.entries)

	def idOf(self, word):
		return self._word_map.get(safe_encode(word), None) if word is not None else None
	id_of = idOf
	
	def contains_word(self, word):
		return self.idOf(word) != None

	def get(self, wid, default=None):
		result = self._id_map.get(wid, default)
		return result

	def __contains__(self, wid):
		return wid in self._id_map
	contains_id = __contains__

	def __getitem__(self, wid):
		return self._id_map[wid]

	def __len__(self):
		return len(self.entries)

	def __iter__(self):
		return iter(self.entries)

	def __add__(self, other):
		unique = self.unique
		entries = set(self.entries)
		if other is not None:
			entries.update(other.entries)
			unique = unique and other.unique
		result = WordBank(entries=list(entries), unique=unique)
		return result

	@CachedProperty('entries')
	def _id_map(self):
		result = {x.wid: x for x in self.entries}
		return result

	@CachedProperty('entries')
	def _word_map(self):
		result = CaseInsensitiveDict()
		result.update({safe_encode(x.word): x.wid for x in self.entries})
		return result

@interface.implementer(IWordEntry)
def _wordentry_adapter(sequence):
	result = WordEntry(wid=to_unicode(sequence[0]), word=to_unicode(sequence[1]))
	if len(sequence) > 2 and sequence[2]:
		result.lang = to_unicode(sequence[2]).lower()
	else:
		result.lang = u'en'

	if len(sequence) > 3 and sequence[3]:
		content = to_unicode(sequence[3])
	else:
		content = result.word
	result.content = HTMLContentFragment(content)
	return result

@interface.implementer(IWordBank)
def _wordbank_adapter(entries, unique=True):
	entries = {e.wid:e for e in entries}
	result = WordBank(entries=tuple(entries.values()), unique=unique)
	return result
