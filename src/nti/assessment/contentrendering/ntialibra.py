#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from plasTeX import Base
from plasTeX.Renderers import render_children

from nti.assessment import parts
from nti.assessment import question
from nti.assessment import interfaces as as_interfaces

from nti.contentfragments import interfaces as cfg_interfaces

from .ntibase import naqvalue
from .ntibase import _AbstractNAQPart
from .ntibase import _LocalContentMixin

###
# Parts
###

class _WordBankMixIn(object):

	def _asm_entries(self):
		result = []
		_naqwordbank = self.getElementsByTagName('naqwordbank')
		if _naqwordbank:
			_naqwordbank = _naqwordbank[0]
			for x in _naqwordbank.getElementsByTagName('naqwordentry'):
				if 'wid' in x.attributes:
					data = [x.attributes['wid'],
							x.attributes['word'],
							x.attributes.get('lang'),
							x._asm_local_content]
					we = as_interfaces.IWordEntry(data)
					result.append(we)
		return _naqwordbank, result

	def _asm_wordbank(self):
		result = None
		_naqwordbank, entries = self._asm_entries()
		if entries:
			result = as_interfaces.IWordBank(entries)
			result.unique = _naqwordbank.attributes.get('unique', 'true') == 'true'
		return result

class naqfillintheblankwithwordbankpart(_AbstractNAQPart, _WordBankMixIn):
	r"""
	A fill in the blank with word bank part.

		\begin{naquestion}
			Arbitrary prefix content goes here.
			\begin{naqfillintheblankwithwordbankpart}
				Arbitrary content for this part goes here.
				\begin{naqinput}
			       	empty fields \naqblankfield{1} \naqblankfield{2} \naqblankfield{3} go here
				\end{naqinput}
				\begin{naqwordbank}
					\naqwordentry{0}{montuno}{es}
					\naqwordentry{1}{tiene}{es}
					\naqwordentry{2}{borinquen}{es}
					\naqwordentry{3}{tierra}{es}
					\naqwordentry{4}{alma}{es}
	            \end{naqwordbank}
	            \begin{naqpaireditems}
					\naqpaireditem{1}{2}
					\naqpaireditem{2}{1}
					\naqpaireditem{3}{0}
				\end{naqpaireditems}
				\begin{naqsolexplanation}
					Arbitrary content explaining how the correct solution is arrived at.
				\end{naqsolexplanation}
			\end{naqfillintheblankwithwordbankpart}
		\end{naquestion}
	"""

	part_factory = parts.QFillInTheBlankWithWordBankPart
	part_interface = as_interfaces.IQFillInTheBlankWithWordBankPart
	soln_interface = as_interfaces.IQFillInTheBlankWithWordBankSolution

	def _asm_object_kwargs(self):
		return { 'wordbank': self._asm_wordbank(),
				 'input': self._asm_input() }

	def _asm_input(self):
		input_el = self.getElementsByTagName('naqinput')[0]
		return cfg_interfaces.HTMLContentFragment(input_el._asm_local_content.strip())

	def _asm_solutions(self):
		solutions = []
		solution_els = self.getElementsByTagName('naqsolution')
		for solution_el in solution_els:
			solution = self.soln_interface(solution_el.answer)
			weight = solution_el.attributes['weight']
			if weight is not None:
				solution.weight = weight
			solutions.append(solution)
		return solutions

	def digest(self, tokens):
		res = super(naqfillintheblankwithwordbankpart, self).digest(tokens)
		if self.macroMode != Base.Environment.MODE_END:
			input_els = self.getElementsByTagName('naqinput')
			assert len(input_els) == 1

			_naqblanks = input_els[0].getElementsByTagName('naqblankfield')
			assert len(input_els) >= 1

			_blankids = {x.attributes.get('id') for x in _naqblanks}
			_blankids.discard(None)
			assert len(_blankids) == len(_naqblanks)

			_naqwordbank = self.getElementsByTagName('naqwordbank')
			assert len(_naqwordbank) <= 1
			if _naqwordbank:
				_naqwordbank = _naqwordbank[0]
				_naqwordentries = _naqwordbank.getElementsByTagName('naqwordentry')
				assert len(_naqwordentries) > 0, "Must specified at least one word entry"
				for x in _naqwordentries:
					assert x.attributes['wid'] and x.attributes['word']

			assert len(self.getElementsByTagName('naqsolutions')) == 0

			naqpaireditems = self.getElementsByTagName('naqpaireditems')
			assert len(naqpaireditems) == 1
			_naqpaireditems = naqpaireditems[0]
			_paireditems = _naqpaireditems.getElementsByTagName('naqpaireditem')
			assert len(_paireditems) == len(_blankids)

			answer = {}
			_naqsolns = self.ownerDocument.createElement('naqsolutions')
			_naqsolns.macroMode = _naqsolns.MODE_BEGIN
			for _item in _paireditems:
				bid = _item.attributes['x']
				wid = _item.attributes['y']
				assert bid and isinstance(bid, six.string_types) and bid in _blankids
				assert wid and isinstance(wid, six.string_types)
				answer[bid] = wid.split(',')
			_naqsoln = self.ownerDocument.createElement('naqsolution')
			_naqsoln.attributes['weight'] = 1.0
			_naqsoln.argSource = '[%s]' % _naqsoln.attributes['weight']
			_naqsoln.answer = answer
			_naqsolns.appendChild(_naqsoln)
			self.insertAfter(_naqsolns, _naqpaireditems)
		return res

class naqfillintheblankshortanswerpart(_AbstractNAQPart):
	r"""
	A fill in the blank short answer part (usually used as the sole part to a question).
	It must have a child listing the regex solutions.  Further the all
	solutions with a weight of 1:: are required to be submitted to receive credit for the
	question

		\begin{naquestion}
			Arbitrary prefix content goes here.
			\begin{naqfillintheblankshortanswerpart}
			    Arbitrary content for this part goes here \naqblankfield{001}[2] \naqblankfield{002}[2]
				\begin{naqregexes}
					\naqregex{001}{.*}  Everything.
					\naqregex{002}{^1\$} Only 1.
	            \end{naqregexes}
				\begin{naqsolexplanation}
					Arbitrary content explaining how the correct solution is arrived at.
				\end{naqsolexplanation}
			\end{naqfillintheblankshortanswerpart}
		\end{naquestion}
	"""

	part_factory = parts.QFillInTheBlankShortAnswerPart
	part_interface = as_interfaces.IQFillInTheBlankShortAnswerPart
	soln_interface = as_interfaces.IQFillInTheBlankShortAnswerSolution

	def _asm_object_kwargs(self):
		return {}

	def _asm_solutions(self):
		solutions = []
		solution_els = self.getElementsByTagName('naqsolution')
		for solution_el in solution_els:
			solution = self.soln_interface(solution_el.answer)
			weight = solution_el.attributes['weight']
			if weight is not None:
				solution.weight = weight
			solutions.append(solution)
		return solutions

	def digest(self, tokens):
		res = super(naqfillintheblankshortanswerpart, self).digest(tokens)
		if self.macroMode != Base.Environment.MODE_END:

			_naqblanks = self.getElementsByTagName('naqblankfield')
			assert len(_naqblanks) >= 1

			_blankids = {x.attributes.get('id') for x in _naqblanks}
			_blankids.discard(None)
			assert len(_blankids) == len(_naqblanks)

			_naqregexes = self.getElementsByTagName('naqregexes')
			assert len(_naqregexes) == 1

			_naqregexes = _naqregexes[0]
			_regentries = _naqregexes.getElementsByTagName('naqregex')
			assert len(_regentries) > 0, "Must specified at least one regex"

			assert len(_blankids) <= len(_regentries)
			assert len(self.getElementsByTagName('naqsolutions')) == 0

			answer = {}
			_naqsolns = self.ownerDocument.createElement('naqsolutions')
			_naqsolns.macroMode = _naqsolns.MODE_BEGIN
			for _naqmregex in _regentries:
				pid, pattern, solution = _naqmregex.attributes['pid'], \
										 _naqmregex.attributes['pattern'], \
										 _naqmregex._asm_local_content
				assert pattern and pid
				answer[pid] = as_interfaces.IRegEx((pattern, solution or None))
			_naqsoln = self.ownerDocument.createElement('naqsolution')
			_naqsoln.answer = answer
			_naqsoln.attributes['weight'] = 1.0
			_naqsoln.argSource = '[%s]' % _naqsoln.attributes['weight']
			_naqsolns.appendChild(_naqsoln)
			self.insertAfter(_naqsolns, _naqregexes)
		return res

class naqregex(naqvalue):
	args = 'pid:str pattern:str:source'

	def invoke(self, tex):
		tok = super(naqregex, self).invoke(tex)
		return tok

	def _after_render(self, rendered):
		self._asm_local_content = rendered

class naqregexes(Base.List):
	pass

class naqpaireditem(naqvalue):
	args = 'x:str y:str'

class naqpaireditems(Base.List):
	args = '[label:idref]'

class naqwordentry(_LocalContentMixin, Base.List.item):
	args = 'wid:str word:str lang:str'

	def _after_render(self, rendered):
		self._asm_local_content = rendered

class naqblankfield(Base.Command):
	args = 'id:str [maxlength:int]'

class naqwordbank(Base.List):
	args = '[unique:str] [label:idref]'

	def invoke(self, tex):
		token = super(naqwordbank, self).invoke(tex)
		if	'unique' in self.attributes and \
			(self.attributes['unique'] or '').lower() == 'unique=false':
			self.attributes['unique'] = 'false'
		else:
			self.attributes['unique'] = 'true'
		return token

class naqwordbankref(Base.Crossref.ref):
	args = '[options:dict] label:idref'

	def digest(self, tokens):
		tok = super(naqwordbankref, self).digest(tokens)
		return tok

class naqregexref(Base.Crossref.ref):
	args = '[options:dict] label:idref'

	def digest(self, tokens):
		tok = super(naqregexref, self).digest(tokens)
		return tok

class naqinput(_LocalContentMixin, Base.Environment):

	def _after_render(self, rendered):
		self._asm_local_content = rendered

###
# Questions
###

from .ntiquestion import naquestion

def _remove_parts_after_render(self, rendered):
	# CS: Make sure we only render the children that do not contain any 'question' part,
	# since those will be rendereds when the part is so.
	def _check(node):
		f = lambda x :isinstance(x, (_AbstractNAQPart,))
		found = any(map(f, node.childNodes)) or f(node)
		return not found

	# each node in self.childNodes is a plasTeX.Base.TeX.Primitives.par
	# check its children to see if they contain any question 'part' objects.
	# do not include them in the asm_local_content
	selected = [n for n in self.childNodes if _check(n)]
	output = render_children(self.renderer, selected)
	output = cfg_interfaces.HTMLContentFragment(''.join(output).strip())
	return output

class naquestionfillintheblankwordbank(naquestion, _WordBankMixIn):

	def _after_render(self, rendered):
		self._asm_local_content = _remove_parts_after_render(self, rendered)

	def _createQuestion(self):
		wordbank = self._asm_wordbank()
		result = question.QFillInTheBlankWithWordBankQuestion(content=self._asm_local_content,
															  parts=self._asm_question_parts(),
															  wordbank=wordbank)
		return result