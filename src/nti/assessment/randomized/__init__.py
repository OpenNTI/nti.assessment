#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import unicode_literals, print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import random
import hashlib

from zope import component

from .interfaces import ISha224Randomized
from .interfaces import IPrincipalSeedSelector

def get_seed(context=None):
	selector = component.queryUtility(IPrincipalSeedSelector)
	result = selector(context) if selector is not None else None
	return result

def randomize(user=None, context=None):
	seed = get_seed(user)	
	if seed is not None:
		use_sha224 = context is not None and ISha224Randomized.providedBy(context)
		if use_sha224:
			hexdigest = hashlib.sha224(bytes(seed)).hexdigest()
			generator = random.Random(long(hexdigest, 16))
		else:
			generator = random.Random(seed)
		return generator
	return None

def shuffle_list(generator, target):
	generator.shuffle(target)
	return target

def questionbank_random(context, user=None):
	generator = random.Random() if context.srand else randomize(user=user, context=context)
	return generator

def questionbank_question_chooser(context, questions=None, user=None):
	result = []
	questions = questions or context.questions
	generator = questionbank_random(context, user=user)
	if generator and questions and context.draw and context.draw < len(questions):
		ranges = context.ranges or ()
		if not ranges:
			sample_idxs = generator.sample(xrange(0, len(questions)), context.draw)
			sample_idxs.sort() # keep order
			result.extend(questions[idx] for idx in sample_idxs)
		else:
			for r in ranges:
				indices = xrange(r.start, r.end+1)
				generated = generator.sample(indices, r.draw)
				for idx in generated:
					result.append(questions[idx])
				generator = questionbank_random(context, user=user)
	else:
		result.extend(questions)
	return result
