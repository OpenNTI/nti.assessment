#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

logger = __import__('logging').getLogger(__name__)


def _patch():
    import os
    import inspect
    import importlib

    from nti.assessment.interfaces import IQPart

    package = '.'.join(__name__.split('.')[:-1])

    ignore_list = ('_patch.py', 'externalization.py', 'jsonschema.py',
                   'externalization.py', 'internalization.py', 'wref.py')

    # set mimetypes on interfaces
    for name in os.listdir(os.path.dirname(__file__)):
        if     name in ignore_list \
            or name[-3:] != '.py' \
            or name.startswith('_'):
            continue

        module = package + '.' + name[:-3]
        module = importlib.import_module(module)

        for _, item in inspect.getmembers(module):
            try:
                mimeType = getattr(item, 'mimeType', None) \
                        or getattr(item, 'mime_type', None)
                if not mimeType:
                    continue
                interfaces = tuple(item.__implemented__.interfaces())
                # first interface is the externalizable object
                root = interfaces[0]
                root.setTaggedValue('_ext_mime_type', mimeType)
                if root.isOrExtends(IQPart):
                    root.setTaggedValue('_ext_jsonschema', 'part')
            except IndexError:  # pragma: no cover
                pass


_patch()
del _patch


def patch():
    pass
