#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import random
import hashlib

from zope import component

from nti.assessment.randomized.interfaces import ISha224Randomized
from nti.assessment.randomized.interfaces import IPrincipalSeedSelector

logger = __import__('logging').getLogger(__name__)


def get_seed(context=None):
    selector = component.queryUtility(IPrincipalSeedSelector)
    result = selector(context) if selector is not None else None
    return result


def randomize(user=None, context=None, seed=None):
    if seed is None:
        seed = get_seed(user)
    seed = int(seed)
    if seed is not None:
        use_sha224 = ISha224Randomized.providedBy(context)
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
    generator = randomize(user=user, context=context)
    return generator


def questionbank_question_index_chooser(context, questions=None, user=None):
    result = ()
    questions = questions or context.questions
    generator = questionbank_random(context, user=user)
    if generator and questions and context.draw and context.draw < len(questions):
        ranges = context.ranges or ()
        if not ranges:
            result = generator.sample(range(0, len(questions)), context.draw)
        else:
            result = []
            for r in ranges:
                indices = range(r.start, r.end + 1)
                generated = generator.sample(indices, r.draw)
                result.extend(generated)
                generator = questionbank_random(context, user=user)
        result.sort()
    else:
        result = range(len(questions))
    return result


def questionbank_question_chooser(context, questions=None, user=None):
    questions = questions or context.questions
    idxs = questionbank_question_index_chooser(context, questions, user)
    if len(idxs) == len(questions):
        result = list(questions)
    else:
        result = [questions[x] for x in idxs]
    return result


def shuffle_matching_part_solutions(generator, values, ext_solutions):
    if not ext_solutions:
        return
    original = {idx: v for idx, v in enumerate(values)}
    shuffled = {
		v: idx for idx, v in enumerate(shuffle_list(generator, values))
	}
    for solution in ext_solutions:
        value = solution['value']
        for k in list(value.keys()):
            idx = int(value[k])
            uidx = shuffled[original[idx]]
            value[k] = uidx


def shuffle_multiple_choice_part_solutions(generator, choices, ext_solutions):
    if not ext_solutions:
        return
    original = {idx: v for idx, v in enumerate(choices)}
    shuffled = {
        v: idx for idx, v in enumerate(shuffle_list(generator, choices))
    }
    for solution in ext_solutions:
        value = int(solution['value'])
        uidx = shuffled[original[value]]
        solution['value'] = uidx


def shuffle_multiple_choice_multiple_answer_part_solutions(generator,
                                                           choices,
                                                           ext_solutions):
    if not ext_solutions:
        return
    original = {idx: v for idx, v in enumerate(choices)}
    shuffled = {
        v: idx for idx, v in enumerate(shuffle_list(generator, choices))
    }
    for solution in ext_solutions:
        value = solution['value']
        for pos, v in enumerate(value):
            idx = int(v)
            uidx = shuffled[original[idx]]
            value[pos] = uidx
