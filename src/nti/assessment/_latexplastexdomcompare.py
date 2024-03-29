#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Support functions for comparing latex Math DOMs using PlasTeX

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from zope.interface.interfaces import ComponentLookupError

from sympy.parsing import sympy_parser

from nti.assessment.interfaces import IQSymbolicMathGrader
from nti.assessment.interfaces import IResponseToSymbolicMathConverter

logger = __import__('logging').getLogger(__name__)


def _math_is_equal(solution, response):
    if solution is None or response is None:
        # We follow the rules for SQL NULL: it's not equal to anything,
        # even itself
        return False
    return _math_children_are_equal(solution.childNodes, response.childNodes) \
        or (_all_text_children(solution) and _all_text_children(response)
            and _text_content_equal(solution, response))
_mathIsEqual = _math_is_equal  # BWC


def _math_children_are_equal(solution, response):
    math1children = _important_child_nodes(solution)
    math2children = _important_child_nodes(response)
    if len(math1children) != len(math2children):
        return False
    for math1child, math2child in zip(math1children, math2children):
        if not _mathChildIsEqual(math1child, math2child):
            return False
    return True
_mathChildrenAreEqual = _math_children_are_equal  # BWC


def _important_child_nodes(childNodes):
    """
    Given the child nodes of a node, return a fresh list of those
    that are important for comparison purposes. Spaces are not considered important.
    """
    return [x for x in childNodes if x.nodeType != x.TEXT_NODE or x.textContent.strip()]
_importantChildNodes = _important_child_nodes  # BWC


def _all_text_children(childNode):
    return all((x.nodeType == x.TEXT_NODE for x in childNode.childNodes))
_allTextChildren = _all_text_children


def _sanitize_text_node_content(textNode):
    text = textNode.textContent.strip()
    text = text.replace(',', '')
    # Whitespace is insignificant
    text = text.replace(' ', '')
    return text
_sanitizeTextNodeContent = _sanitize_text_node_content


def _text_content_equal(child1, child2):
    """
    Checks to see if the two nodes have equivalent text. If they compare
    equal from a purely textual standpoint, then that is the answer. Otherwise,
    we try to compare them from a symbolic version of their text.
    """
    return _sanitize_text_node_content(child1) == _sanitize_text_node_content(child2) \
        or _symbolic(child1) == _symbolic(child2)


def _symbolic(child):
    """
    Returns a symbolic version of the child, if possible. Always
    returns something that will be valid for an equality test
    with other objects given to this method (i.e., should not return None).
    """
    try:
        return sympy_parser.parse_expr(child.textContent)
    # TypeError arises on 1(2) -> function call of 1
    except (sympy_parser.TokenError, SyntaxError, AttributeError, TypeError):
        return child
    except NameError:
        # sympy 0.7.2 and 0.7.3 has a bug: in
        # sympy.parsing.sympy_tokenize (line 318 in 0.7.3) it wants to
        # raise TokenError, instead raises NameError on "'''" In
        # general, even github trunk (as-of 20131006) has problems
        # parsing multi-line continued strings. The file is full of
        # 'strstart' refs to undefined variables.
        # See https://github.com/sympy/sympy/issues/2515
        # We have a test case for this.
        return child
    except MemoryError:
        # On some deeply nested expressions that are incredibly
        # unlikely in real life, sympy can overflow the stack
        # ("s_push: parser stack overflow" is printed to console). See
        # the test case. Hopefully this correctly reclaims memory.
        return child


def _all_math_children_are_equal(child1, child2):
    return all((_math_child_is_equal(child1.attributes[k.name], child2.attributes[k.name])
                for k in child1.arguments))


def _len_important_children_nodes_are_equal(child1, child2):
    important_children_1 = _important_child_nodes(child1.childNodes)
    important_children_2 = _important_child_nodes(child2.childNodes)
    return len(important_children_1) == len(important_children_2)


def _math_child_is_equal(child1, child2):
    # If are children aren't even the same type they are probably not equal
    # If they are actually the same thing (only happens in None case I think)
    if child1 == child2:
        return True

    if     child1.nodeType != child2.nodeType \
        or not _len_important_children_nodes_are_equal(child1, child2):
        return False

    if child1.nodeType == child1.TEXT_NODE:
        text1 = _sanitizeTextNodeContent(child1)
        text2 = _sanitizeTextNodeContent(child2)
        return type(text1) == type(text2) and text1 == text2

    if child1.nodeType == child1.ELEMENT_NODE:
        # Check that the arguments and the children are equal
        return (
            len(child1.arguments) == len(child2.arguments)
            and _all_math_children_are_equal(child1, child2)
            and (
                (_all_text_children(child1)
                    and _all_text_children(child2)
                    and _text_content_equal(child1, child2))
                or
                _math_children_are_equal(
                    child1.childNodes, child2.childNodes)
            )
        )

    if child1.nodeType == child1.DOCUMENT_FRAGMENT_NODE:
        return _math_children_are_equal(child1.childNodes, child2.childNodes)

    # Fallback to string comparison
    return _sanitize_text_node_content(child1) == _sanitize_text_node_content(child2)

_mathChildIsEqual = _math_child_is_equal  # BWC
_stripEmptyChildren = _important_child_nodes  # BWC


def grade(solution, response):
    __traceback_info__ = solution, response
    try:
        converter = component.getMultiAdapter((solution, response),
                                              IResponseToSymbolicMathConverter)
    except ComponentLookupError:  # pragma: no cover
        logger.warning("Unable to grade math, assuming wrong", exc_info=True)
        return False

    def _grade(s, r):
        solution_dom = converter.convert(s)
        response_dom = converter.convert(r)
        return _mathIsEqual(solution_dom, response_dom)

    # TODO: This basic algorithm is similar to
    # graders.UnitAwareFloatEqualityGrader
    if solution.allowed_units is None:  # No special unit handling
        return _grade(solution, response)

    if not solution.allowed_units:  # Units are specifically forbidden
        return _grade(solution, response)

    # Units may be required, or optional if the last element is the empty
    # string
    allowed_units = solution.allowed_units
    if u'\uFF05' in allowed_units and '\\%' not in allowed_units:
        # The full-width percent is how we tend to write percents in source files
        # we also want to handle how they come in from the browser, in "\%"
        # (https://trello.com/c/4qdjExxV)
        allowed_units = list(allowed_units)
        # keep these two together, optional must come at end
        allowed_units.insert(allowed_units.index(u'\uFF05'), '\\%')

    # Before doing this, strip off opening and closing latex display math signs, if they were sent,
    # so that we can check for units
    # Only do this if *both* were provided
    response_value = response.value
    if      response_value and response_value.startswith('$') \
        and response_value.endswith('$') and len(response_value) > 2:
        response_value = response_value[1:-1]

    for unit in allowed_units:
        if response_value.endswith(unit):
            # strip the trailing unit and grade.
            # This handles unit='cm' and value in ('1.0 cm', '1.0cm')
            # It also handles unit='', if it comes at the end
            value = response_value[:-len(unit)] if unit else response_value
            __traceback_info__ = response_value, unit, value
            return _grade(solution, type(response)(value.strip()))

    # If we get here, there was no unit that matched. Therefore, units were required
    # and not given
    return False


@interface.implementer(IQSymbolicMathGrader)
class Grader(object):

    def __init__(self, unused_part, solution, response):
        self.solution = solution
        self.response = response

    def __call__(self):
        result = grade(self.solution, self.response)
        if      not result and not self.response.value.startswith('<') \
            and self.solution.allowed_units is None:
            # Hmm. Is there some trailing text we should brush away from the response?
            # Only try if it's not OpenMath XML (which only comes up in test cases now)
            # NOTE: We now only do this if "default" handling of units is specified; otherwise,
            # it would already be handled.
            # NOTE: This is legacy code and can and should go away as soon as all
            # content is annotated with units.
            def _regrade(value):
                response = type(self.response)(value)
                result = grade(self.solution, response)
                if result:
                    self.response = response
                return result

            # strip anything after the last space
            parts = self.response.value.rsplit(' ', 1)
            if len(parts) == 2:
                result = _regrade(parts[0])
            # this percent handling is added after the unit handling, so it is special cased
            # since this is a legacy code path. https://trello.com/c/4qdjExxV
            elif self.response.value.endswith('\\%'):
                result = _regrade(self.response.value[:-2])
            elif    self.response.value.endswith('\\%$') \
                and self.response.value.startswith('$'):
                result = _regrade(self.response.value[1:-3])
        return result
