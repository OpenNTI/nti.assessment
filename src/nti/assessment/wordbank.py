#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from functools import total_ordering

from requests.structures import CaseInsensitiveDict

import six

from zope import interface

from zope.cachedescriptors.property import CachedProperty

from zope.container.contained import Contained

from persistent import Persistent

from nti.assessment.interfaces import IWordBank
from nti.assessment.interfaces import IWordEntry

from nti.base._compat import text_

from nti.contentfragments.interfaces import IHTMLContentFragment

from nti.externalization.representation import WithRepr

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


def safe_encode(word, encoding="UTF-8"):
    word = str(word) if not isinstance(word, six.string_types) else word
    try:
        word = word.encode(encoding)
    except Exception:  # pylint: disable=broad-except
        word = repr(word)
    return word


@WithRepr
@total_ordering
@interface.implementer(IWordEntry)
class WordEntry(Persistent, SchemaConfigured, Contained):
    createDirectFieldProperties(IWordEntry)

    __external_can_create__ = True
    mime_type = mimeType = 'application/vnd.nextthought.naqwordentry'

    wid = None
    word = None
    lang = u'en'

    def __init__(self, *args, **kwargs):
        Persistent.__init__(self)
        SchemaConfigured.__init__(self, *args, **kwargs)

    def __eq__(self, other):
        try:
            return self is other or self.wid == other.wid
        except AttributeError:
            return NotImplemented

    def __hash__(self):
        xhash = 47
        xhash ^= hash(self.wid)
        return xhash

    def __lt__(self, other):
        try:
            return (self.word.lower(), self.lang) < (other.word.lower(), other.self.lang)
        except AttributeError:
            return NotImplemented

    def __gt__(self, other):
        try:
            return (self.word.lower(), self.lang) > (other.word.lower(), other.self.lang)
        except AttributeError:
            return NotImplemented


@WithRepr
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
        return frozenset(x.word for x in self.entries)

    @CachedProperty('entries')
    def ids(self):
        return frozenset(x.wid for x in self.entries)

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

    def __eq__(self, other):
        try:
            return self is other or (self.ids, self.unique) == (other.ids, other.unique)
        except AttributeError:
            return NotImplemented

    def __hash__(self):
        xhash = 47
        xhash ^= hash(self.ids)
        xhash ^= hash(self.unique)
        return xhash

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
        return WordBank(entries=list(entries), unique=unique)

    @CachedProperty('entries')
    def _id_map(self):
        return {x.wid: x for x in self.entries}

    @CachedProperty('entries')
    def _word_map(self):
        result = CaseInsensitiveDict()
        result.update({safe_encode(x.word): x.wid for x in self.entries})
        return result


@interface.implementer(IWordEntry)
def _wordentry_adapter(sequence):
    result = WordEntry(wid=text_(sequence[0]),
                       word=text_(sequence[1]))
    if len(sequence) > 2 and sequence[2]:
        result.lang = text_(sequence[2]).lower()
    else:
        result.lang = u'en'

    if len(sequence) > 3 and sequence[3]:
        content = text_(sequence[3])
    else:
        content = result.word
    result.content = IHTMLContentFragment(content)
    return result


@interface.implementer(IWordBank)
def _wordbank_adapter(entries, unique=True):
    entries = {e.wid: e for e in entries}
    result = WordBank(entries=tuple(entries.values()), unique=unique)
    return result
