#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
A macro package to support the writing of assessments inline with
the rest of content.

These are rendered into HTML as ``<object>`` tags with an NTIID
that matches an object to resolve from the dataserver. The HTML inside the object may or may
not be usable for basic viewing; client applications will use the Question object
from the dataserver to guide the ultimate rendering.

Example::

	\begin{naquestion}[individual=true]
		Arbitrary prefix content goes here. This may be rendered to the document.

		Questions consist of sequential parts, often just one part. The parts
		do not have to be homogeneous.
		\begin{naqsymmathpart}
		   Arbitrary content for this part goes here. This may be rendered to the document.

		   A part has one or more possible solutions. The solutions are of the same type,
		   determined implicitly by the part type.
		   \begin{naqsolutions}
			   \naqsolution[weight]<unit1, unit2> A possible solution. The weight, defaulting to one,
				   	is how "correct" this solution is. Some parts may have more compact
					representations of solutions.

					The units are only valid on math parts. If given, it may be an empty list  to specify
					that units are forbidden, or a list of optional units that may be included as part of the
					answer.
			\end{naqsolutions}
			\begin{naqhints}
				\naqhint Arbitrary content giving a hint for how to arrive at the correct
					solution.
			\end{naqhints}
			\begin{naqsolexplanation}
				Arbitrary content explaining how the correct solution is arrived at.
			\end{naqsolexplanation}
		\end{naqsymmathpart}
	\end{naquestion}

The TeX macro objects that correspond to \"top-level\" assessment objects
(those defined in :mod:`nti.assessment.interfaces`) will implement a method
called ``assessment_object``. This method can be called *after* the rendering
process is complete to gain the desired object. This object can then be
externalized or otherwise processed; this object is not itself part of
the TeX DOM.

.. $Id$
"""
# All of these have too many public methods
# pylint: disable=R0904

# "not callable" for the default values of None
# pylint: disable=E1102

# access to protected members -> _asm_local_content defined in this module
# pylint: disable=W0212

# "Method __delitem__ is abstract in Node and not overridden"
# pylint: disable=W0223

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import six
from six import text_type
import itertools

from zope import schema
from zope import interface
from zope.cachedescriptors.method import cachedIn
from zope.mimetype.interfaces import mimeTypeConstraint
from zope.cachedescriptors.property import readproperty

from persistent.list import PersistentList

from plasTeX import Base
from plasTeX.Base import Crossref
from plasTeX.Renderers import render_children
from plasTeX.interfaces import IOptionAwarePythonPackage

from nti.externalization.datetime import datetime_from_string

from nti.assessment import parts
from nti.assessment import question
from nti.assessment import assignment
from nti.assessment import interfaces as as_interfaces
from nti.assessment.randomized import parts as randomized_parts
from nti.assessment.randomized import interfaces as rand_interfaces

from nti.contentfragments import interfaces as cfg_interfaces

from nti.contentrendering import plastexids
from nti.contentrendering import interfaces as crd_interfaces
from nti.contentrendering.plastexpackages.ntilatexmacros import ntiincludevideo
from nti.contentrendering.plastexpackages._util import LocalContentMixin as _BaseLocalContentMixin

from paste.deploy.converters import asbool

class _LocalContentMixin(_BaseLocalContentMixin):
	# SAJ: HACK. Something about naqvideo and _LocalContentMixin? ALl the parts
	# and solutions from this module are excluded from rendering
	_asm_ignorable_renderables = ()

# Handle custom counter names
class naquestionsetname(Base.Command):
	unicode = ''

class naquestionname(Base.Command):
	unicode = ''

class naqsolutionnumname(Base.Command):
	unicode = ''

class naqsolutions(Base.List):

	counters = ['naqsolutionnum']
	args = '[ init:int ]'

	def invoke( self, tex ):
		# TODO: Why is this being done?
		res = super(naqsolutions, self).invoke( tex )

		if 'init' in self.attributes and self.attributes['init']:
			self.ownerDocument.context.counters[self.counters[0]].setcounter( self.attributes['init'] )
		elif self.macroMode != Base.Environment.MODE_END:
			self.ownerDocument.context.counters[self.counters[0]].setcounter(0)

		return res

	def digest( self, tokens ):
		# After digesting loop back over the children moving nodes before
		# the first item into the first item
		# TODO: Why is this being done?
		res = super(naqsolutions, self).digest(tokens)
		if self.macroMode != Base.Environment.MODE_END:
			nodesToMove = []

			for node in self:

				if isinstance(node, Base.List.item):
					nodesToMove.reverse()
					for nodeToMove in nodesToMove:
						self.removeChild(nodeToMove)
						node.insert(0, nodeToMove)
					break

				nodesToMove.append(node)

		return res

_LocalContentMixin._asm_ignorable_renderables += (naqsolutions,)

class naqsolution(Base.List.item):

	args = '[weight:float] <units>'

	# We use <> for the units list because () looks like a geometric
	# point, and there are valid answers like that.
	# We also do NOT use the :list conversion, because if the units list
	# has something like an (escaped) % in it, plasTeX fails to tokenize the list
	# Instead, we work with the TexFragment object ourself

	def invoke( self, tex ):
		# TODO: Why is this being done? Does the counter matter?
		self.counter = naqsolutions.counters[0]
		self.position = self.ownerDocument.context.counters[self.counter].value + 1
		#ignore the list implementation
		return Base.Command.invoke(self,tex)

	def units_to_text_list(self):
		"""Find the units, if any, and return a list of their text values"""
		units = self.attributes.get( 'units' )
		if units:
			# Remove trailing delimiter and surrounding whitespace. For consecutive
			# text parts, we have to split ourself
			result = []
			for x in units:
				# We could get elements (Macro/Command) or strings (plastex.dom.Text)
				if getattr( x, 'tagName', None ) == 'math':
					raise ValueError( "Math cannot be roundtripped in units. Try unicode symbols" )
				x = unicode(x).rstrip( ',' ).strip()
				result.extend( x.split( ',' ) )
			return result

	def units_to_html(self):
		units = self.units_to_text_list()
		if units:
			return ','.join( units )

_LocalContentMixin._asm_ignorable_renderables += (naqsolution,)

class naqsolexplanation(_LocalContentMixin, Base.Environment):
	pass

_LocalContentMixin._asm_ignorable_renderables += (naqsolexplanation,)

class _AbstractNAQPart(_LocalContentMixin, Base.Environment):

	randomize = False

	#: Defines the type of part this maps too
	part_interface = None

	#: Defines the type of solution this part produces.
	#: Solution objects will be created by adapting the text content of the solution DOM nodes
	#: into this interface.
	soln_interface = None

	part_factory = None
	hint_interface = as_interfaces.IQHTMLHint

	args = '[randomize:str]'

	def _asm_solutions(self):
		"""
		Returns a list of solutions (of the type identified in ``soln_interface``).
		This implementation investigates the child nodes of this object; subclasses
		may do something different.

		"""
		solutions = []
		solution_els = self.getElementsByTagName( 'naqsolution' )
		for solution_el in solution_els:
			#  If the textContent is taken instead of the source of the child element, the
			#  code fails on Latex solutions like $\frac{1}{2}$
			# TODO: Should this be rendered? In some cases yes, in some cases no?
			content = ' '.join([c.source.strip() for c in solution_el.childNodes]).strip()
			if len(content) >= 2 and content.startswith( '$' ) and content.endswith( '$' ):
				content = content[1:-1]

			# Note that this is already a latex content fragment, we don't need
			# to adapt it with the interfaces. If we do, a content string like "75\%" becomes
			# "75\\\\%\\", which is clearly wrong
			sol_text = unicode(content).strip()
			solution = self.soln_interface(cfg_interfaces.LatexContentFragment(sol_text))
			weight = solution_el.attributes['weight']
			if weight is not None:
				solution.weight = weight

			if self.soln_interface.isOrExtends( as_interfaces.IQMathSolution ):
				# Units given? We currently always make units optional, given or not
				# This can easily be changed or configured
				allowed_units = solution_el.units_to_text_list()
				if not allowed_units:
					allowed_units = ('',)
				if '' not in allowed_units:
					allowed_units = list(allowed_units)
					allowed_units.append( '' )
				solution.allowed_units = allowed_units
			solutions.append( solution )

		return solutions

	def _asm_explanation(self):
		exp_els = self.getElementsByTagName( 'naqsolexplanation' )
		assert len(exp_els) <= 1
		if exp_els:
			return exp_els[0]._asm_local_content
		return cfg_interfaces.ILatexContentFragment( '' )

	def _asm_hints(self):
		"""
		Collects the ``naqhint`` tags found beneath this element,
		converts them to the type of object identified by ``hint_interface``,
		and returns them in a list. For use by :meth:`assessment_object`
		"""
		hints = []
		hint_els = self.getElementsByTagName('naqhint')
		for hint_el in hint_els:
			hint = self.hint_interface( hint_el._asm_local_content )
			hints.append( hint )
		return hints

	def _asm_object_kwargs(self):
		"""
		Subclasses may override this to return a dictionary of keyword
		arguments to pass to ``part_factory`` when creating
		the corresponding assessment object.
		"""
		return {}

	@cachedIn('_v_assessment_object')
	def assessment_object( self ):
		# Be careful to turn textContent into plain unicode objects, not
		# plastex Text subclasses, which are also expensive nodes.
		result = self.part_factory( content=self._asm_local_content,
									solutions=self._asm_solutions(),
									explanation=self._asm_explanation(),
									hints=self._asm_hints(),
									**self._asm_object_kwargs()	)

		errors = schema.getValidationErrors( self.part_interface, result )
		if errors: # pragma: no cover
			__traceback_info__ = self.part_interface, errors, result
			raise errors[0][1]
		return result

	def _after_render( self, rendered ):
		super(_AbstractNAQPart,self)._after_render( rendered )
		# The hints and explanations don't normally get rendered
		# by the templates, so make sure they do
		for x in itertools.chain(self.getElementsByTagName('naqsolexplanation'),
								 self.getElementsByTagName('naqsolution'),
								 self.getElementsByTagName('naqhint'),
								 self.getElementsByTagName('naqchoice'),
								 self.getElementsByTagName('naqmlabel'),
								 self.getElementsByTagName('naqmvalue')):
			unicode(x)

	def invoke(self, tex):
		token = super(_AbstractNAQPart, self).invoke(tex)
		if	'randomize' in self.attributes and \
			(self.attributes['randomize'] or '').lower() == 'randomize=true':
			self.randomize = True
			self.attributes['randomize'] = 'true'
		else:
			self.randomize = False
			self.attributes['randomize'] = 'false'
		return token

_LocalContentMixin._asm_ignorable_renderables += (_AbstractNAQPart,)

# NOTE: Part Node's MUST be named 'naq'XXX'part'

class naqnumericmathpart(_AbstractNAQPart):
	"""
	Solutions are treated as numbers for the purposes of grading.
	"""

	part_factory = parts.QNumericMathPart
	part_interface = as_interfaces.IQNumericMathPart
	soln_interface = as_interfaces.IQNumericMathSolution

class naqsymmathpart(_AbstractNAQPart):
	"""
	Solutions are treated symbolicaly for the purposes of grading.
	"""

	part_factory = parts.QSymbolicMathPart
	part_interface = as_interfaces.IQSymbolicMathPart
	soln_interface = as_interfaces.IQLatexSymbolicMathSolution

class naqfreeresponsepart(_AbstractNAQPart):
	part_factory = parts.QFreeResponsePart
	part_interface = as_interfaces.IQFreeResponsePart
	soln_interface = as_interfaces.IQFreeResponseSolution

class naqmodeledcontentpart(_AbstractNAQPart):
	"""
	This is a base part, and while it matches our internal
	implementation, it is not actually meant for authoring.
	External intent is better expressed with :class:`naqessaypart`
	"""
	soln_interface = None
	part_factory = parts.QModeledContentPart
	part_interface = as_interfaces.IQModeledContentPart

class naqessaypart(naqmodeledcontentpart):
	r"""
	A part having a body that is intended to be large (multi-paragraphs)
	potentially even containing whiteboards. This part CANNOT
	be auto-graded and has no solution.

	Example::

		\begin{naquestion}[individual=true]
			Arbitrary content goes here.
			\begin{naqessaypart}
			Arbitrary content goes here.
			\begin{naqhints}
				\naqhint Some hint
			\end{naqhints}
			\end{naqessaypart}
		\end{naquestion}
	"""

class naqmultiplechoicepart(_AbstractNAQPart):
	r"""
	A multiple-choice part (usually used as the sole part to a question).
	It must have a child listing the possible choices; the solutions are collapsed
	into this child; at least one of them must have a weight equal to 1::

		\begin{naquestion}
			Arbitrary prefix content goes here.
			\begin{naqmultiplechoicepart}
			   Arbitrary content for this part goes here.
			   \begin{naqchoices}
			   		\naqchoice Arbitrary content for the choice.
					\naqchoice[1] Arbitrary content for this choice; this is the right choice.
					\naqchoice[0.5] This choice is half correct.
				\end{naqchoices}
				\begin{naqsolexplanation}
					Arbitrary content explaining how the correct solution is arrived at.
				\end{naqsolexplanation}
			\end{naqmultiplechoicepart}
		\end{naquestion}
	"""

	part_factory = parts.QMultipleChoicePart
	part_interface = as_interfaces.IQMultipleChoicePart
	soln_interface = as_interfaces.IQMultipleChoiceSolution

	#forcePars = True

	def _asm_choices(self):
		return [x._asm_local_content for x in self.getElementsByTagName( 'naqchoice' )]

	def _asm_object_kwargs(self):
		return { 'choices': self._asm_choices() }

	def digest( self, tokens ):
		res = super(naqmultiplechoicepart,self).digest( tokens )
		# Validate the document structure: we have a naqchoices child with
		# at least two of its own children, and at least one weight == 1. There is no explicit solution
		_naqchoices = self.getElementsByTagName( 'naqchoices' )
		assert len(_naqchoices) == 1
		_naqchoices = _naqchoices[0]
		assert len(_naqchoices) > 1, "Must have more than one choice"
		assert any( (_naqchoice.attributes['weight'] == 1.0 for _naqchoice in _naqchoices) )
		assert len(self.getElementsByTagName( 'naqsolutions' )) == 0

		# Tranform the implicit solutions into explicit 0-based solutions
		_naqsolns = self.ownerDocument.createElement( 'naqsolutions' )
		_naqsolns.macroMode = self.MODE_BEGIN
		for i, _naqchoice in enumerate(_naqchoices):
			if _naqchoice.attributes['weight']:
				_naqsoln = self.ownerDocument.createElement( 'naqsolution' )
				_naqsoln.attributes['weight'] = _naqchoice.attributes['weight']
				# Also put the attribute into the argument source, for presentation
				_naqsoln.argSource = '[%s]' % _naqsoln.attributes['weight']
				_naqsoln.appendChild( self.ownerDocument.createTextNode( str(i) ) )
				_naqsolns.appendChild( _naqsoln )
		self.insertAfter( _naqsolns, _naqchoices )
		return res

	def invoke(self, tex):
		token = super(naqmultiplechoicepart, self).invoke(tex)
		if self.randomize:
			self.part_factory = randomized_parts.QRandomizedMultipleChoicePart
			self.part_interface = rand_interfaces.IQRandomizedMultipleChoicePart
		return token

class naqmultiplechoicemultipleanswerpart(_AbstractNAQPart):
	r"""
	A multiple-choice / multiple-answer part (usually used as the sole part to a question).
	It must have a child listing the possible choices; the solutions are collapsed
	into this child; at least one of them must have a weight equal to 1::.  Further the all
	solutions with a weight of 1:: are required to be submitted to receive credit for the
	question

		\begin{naquestion}
			Arbitrary prefix content goes here.
			\begin{naqmultiplechoicemultipleanswerpart}
			        Arbitrary content for this part goes here.
				\begin{naqchoices}
			   		\naqchoice Arbitrary content for the choices.
					\naqchoice[1] This is one part of a right choice.
					\naqchoice[1] This is another part of a right choice.
	                        \end{naqchoices}
				\begin{naqsolexplanation}
					Arbitrary content explaining how the correct solution is arrived at.
				\end{naqsolexplanation}
			\end{naqmultiplechoicemultipleanswerpart}
		\end{naquestion}
	"""

	part_factory = parts.QMultipleChoiceMultipleAnswerPart
	part_interface = as_interfaces.IQMultipleChoiceMultipleAnswerPart
	soln_interface = as_interfaces.IQMultipleChoiceMultipleAnswerSolution

	def _asm_choices(self):
		return [x._asm_local_content for x in self.getElementsByTagName( 'naqchoice' )]

	def _asm_object_kwargs(self):
		return { 'choices': self._asm_choices() }

	def _asm_solutions(self):
		solutions = []
		# By definition, there can only be one solution element.
		solution_el = self.getElementsByTagName( 'naqsolution' )[0]
		solution = self.soln_interface( solution_el.answer )
		weight = solution_el.attributes['weight']
		if weight is not None:
			solution.weight = weight
		solutions.append(solution)
		return solutions

	def digest( self, tokens ):
		res = super(naqmultiplechoicemultipleanswerpart, self).digest(tokens)
		# Validate the document structure: we have a naqchoices child
		# with at least two of its own children, and at least one
		# weight == 1.  There is no explicit solution
		_naqchoices = self.getElementsByTagName( 'naqchoices' )
		assert len(_naqchoices) == 1

		_naqchoices = _naqchoices[0]
		assert len(_naqchoices) > 1, "Must have more than one choice"
		assert any( (_naqchoice.attributes['weight'] == 1.0 for _naqchoice in _naqchoices) )
		assert len(self.getElementsByTagName( 'naqsolutions' )) == 0

		# Tranform the implicit solutions into a list of 0-based indices.
		_naqsolns = self.ownerDocument.createElement( 'naqsolutions' )
		_naqsolns.macroMode = _naqsolns.MODE_BEGIN
		_naqsoln = self.ownerDocument.createElement( 'naqsolution' )
		_naqsoln.attributes['weight'] = 1.0
		_naqsoln.argSource = '[1.0]'
		_naqsoln.answer = []
		for i, _naqchoice in enumerate(_naqchoices):
			if _naqchoice.attributes['weight'] and _naqchoice.attributes['weight'] == 1:
				_naqsoln.answer.append( i )
		_naqsolns.appendChild( _naqsoln )
		self.insertAfter( _naqsolns, _naqchoices )
		return res

	def invoke(self, tex):
		token = super(naqmultiplechoicemultipleanswerpart, self).invoke(tex)
		if self.randomize:
			self.part_factory = randomized_parts.QRandomizedMultipleChoiceMultipleAnswerPart
			self.part_interface = rand_interfaces.IQRandomizedMultipleChoiceMultipleAnswerPart
		return token

class naqfilepart(_AbstractNAQPart):
	r"""
	A part specifying that the user must upload a file::

	   \begin{naquestion}
	       Arbitrary prefix content.
		   \begin{naqfilepart}(application/pdf,text/*,.txt)[1024]
		      Arbitrary part content.
		   \end{naqfilepart}
		\end{naquestion}

	An (effectively required) argument in parenthesis is a list of
	mimetypes and file extensions to allow; to allow arbitrary types
	use ``*/*,*`` (the former allows all mime types, the latter allows
	all extensions). As another example, to allow PDF files with any
	extension, use ``application/pdf,*`` or to allow anything that might
	be a PDF, try ``*/*,.pdf``. A good list for documents might be
	``*/*,.txt,.doc,.docx,.pdf``

	The optional argument in square brackets is the max size of the
	file in kilobytes; the example above thus specifies a 1MB cap.
	"""

	args = "(types:list:str)[size:int]"

	part_interface = as_interfaces.IQFilePart
	part_factory = parts.QFilePart
	soln_interface = None

	_max_file_size = None
	_allowed_mime_types = ()
	_allowed_extensions = ()

	@property
	def allowed_mime_types(self):
		return ','.join(self._allowed_mime_types) if self._allowed_mime_types else None

	def _asm_solutions(self):
		"Solutions currently unsupported"
		return ()

	def _asm_object_kwargs(self):
		kw = {}
		for k in 'allowed_extensions', 'allowed_mime_types', 'max_file_size':
			mine = getattr(self, '_' + k)
			if mine:
				kw[k] = mine
		return kw

	def digest( self, tokens ):
		res = super(naqfilepart,self).digest(tokens)

		if self.attributes.get('size'):
			self._max_file_size = self.attributes['size'] * 1024 # KB to bytes
		if self.attributes.get('types'):
			for mime_or_ext in self.attributes['types']:
				if mimeTypeConstraint(mime_or_ext):
					self._allowed_mime_types += (mime_or_ext,)
				elif mime_or_ext.startswith('.') or mime_or_ext == '*':
					self._allowed_extensions += (mime_or_ext,)
				else: # pragma: no cover
					raise ValueError("Type is not MIME, extension, or wild", mime_or_ext )
		return res

class naqmatchingpart(_AbstractNAQPart):
	r"""
	A matching part (usually used as the sole part to a question).
	It must have two children, one listing the possible labels, with the
	correct solution's index in brackets, and the other listing the possible
	values::

		\begin{naquestion}
			Arbitrary prefix content goes here.
			\begin{naqmatchingpart}
			   Arbitrary content for this part goes here.
			   \begin{naqmlabels}
			   		\naqmlabel[2] What is three times two?
					\naqmlabel[0] What is four times three?
					\naqmlabel[1] What is five times two thousand?
				\end{naqmlabels}
				\begin{naqmvalues}
					\naqmvalue Twelve
					\naqmvalue Ten thousand
					\naqmvalue Six
				\end{naqmvalues}
				\begin{naqsolexplanation}
					Arbitrary content explaining how the correct solution is arrived at.
				\end{naqsolexplanation}
			\end{naqmatchingpart}
		\end{naquestion}
	"""

	part_factory = parts.QMatchingPart
	part_interface = as_interfaces.IQMatchingPart
	soln_interface = as_interfaces.IQMatchingSolution

	#forcePars = True

	def _asm_labels(self):
		return [x._asm_local_content for x in self.getElementsByTagName( 'naqmlabel' )]

	def _asm_values(self):
		return [x._asm_local_content for x in self.getElementsByTagName( 'naqmvalue' )]

	def _asm_object_kwargs(self):
		return { 'labels': self._asm_labels(),
				 'values': self._asm_values() }

	def _asm_solutions(self):
		solutions = []
		solution_els = self.getElementsByTagName('naqsolution')
		for solution_el in solution_els:
			solution = self.soln_interface( solution_el.answer )
			weight = solution_el.attributes['weight']
			if weight is not None:
				solution.weight = weight
			solutions.append( solution )
		return solutions

	def digest( self, tokens ):
		res = super(naqmatchingpart,self).digest( tokens )
		# Validate the document structure: we have a naqlabels child with
		# at least two of its own children, an naqvalues child of equal length
		# and a proper matching between the two
		if self.macroMode != Base.Environment.MODE_END:
			_naqmlabels = self.getElementsByTagName('naqmlabels')
			assert len(_naqmlabels) == 1
			_naqmlabels = _naqmlabels[0]
			assert len(_naqmlabels) > 1, "Must have more than one label; instead got: " + \
										 str([x for x in _naqmlabels])

			_naqmvalues = self.getElementsByTagName('naqmvalues')
			assert len(_naqmvalues) == 1
			_naqmvalues = _naqmvalues[0]
			assert len(_naqmvalues) == len(_naqmlabels), "Must have exactly one value per label"

			for i in range(len(_naqmlabels)):
				assert any( (_naqmlabel.attributes['answer'] == i for _naqmlabel in _naqmlabels) )
			assert len(self.getElementsByTagName('naqsolutions')) == 0

			# Tranform the implicit solutions into an array
			answer = {}
			_naqsolns = self.ownerDocument.createElement('naqsolutions')
			_naqsolns.macroMode = _naqsolns.MODE_BEGIN
			for i, _naqmlabel in enumerate(_naqmlabels):
				answer[i] = _naqmlabel.attributes['answer']
			_naqsoln = self.ownerDocument.createElement('naqsolution')
			_naqsoln.attributes['weight'] = 1.0

			# Also put the attribute into the argument source, for presentation
			_naqsoln.argSource = '[%s]' % _naqsoln.attributes['weight']
			_naqsoln.answer = answer
			_naqsolns.appendChild( _naqsoln )
			self.insertAfter( _naqsolns, _naqmvalues)
		return res

	def invoke(self, tex):
		token = super(naqmatchingpart, self).invoke(tex)
		if self.randomize:
			self.part_factory = randomized_parts.QRandomizedMatchingPart
			self.part_interface = rand_interfaces.IQRandomizedMatchingPart
		return token

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

			_naqsolns = self.ownerDocument.createElement('naqsolutions')
			_naqsolns.macroMode = _naqsolns.MODE_BEGIN
			answer = {}
			for _naqmregex in _regentries:
				pid, pattern = _naqmregex.attributes['pid'], _naqmregex.attributes['pattern']
				assert pattern and pid
				answer[pid] = pattern
			_naqsoln = self.ownerDocument.createElement('naqsolution')
			_naqsoln.attributes['weight'] = 1.0
			_naqsoln.argSource = '[%s]' % _naqsoln.attributes['weight']
			_naqsoln.answer = answer
			_naqsolns.appendChild(_naqsoln)
			self.insertAfter(_naqsolns, _naqregexes)
		return res

_LocalContentMixin._asm_ignorable_renderables += (naqfillintheblankshortanswerpart,)

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

_LocalContentMixin._asm_ignorable_renderables += (_WordBankMixIn,)

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

_LocalContentMixin._asm_ignorable_renderables += (naqfillintheblankwithwordbankpart,)

class naqchoices(Base.List):
	pass

class naqmlabels(Base.List):
	pass

class naqmvalues(Base.List):
	pass

class naqvalue(_LocalContentMixin, Base.List.item):

	@readproperty
	def _asm_local_content(self):
		return cfg_interfaces.ILatexContentFragment(unicode(self.textContent).strip())

class naqchoice(naqvalue):
	args = "[weight:float]"

class naqmlabel(naqvalue):
	args = "[answer:int]"

class naqmvalue(naqvalue):
	pass

class naqregex(naqvalue):
	args = 'pid:str pattern:str:source'

	def invoke(self, tex):
		tok = super(naqregex, self).invoke(tex)
		return tok

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

	def digest(self, tokens):
		res = super(naqblankfield, self).digest(tokens)
		return res

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

_LocalContentMixin._asm_ignorable_renderables += (naqinput,)

class naqordereditem(naqvalue):
	args = 'id:str'

class naqordereditems(Base.List):
	pass

class naqhints(Base.List):
	pass

class naqhint(_LocalContentMixin,Base.List.item):

	def _after_render( self, rendered ):
		self._asm_local_content = rendered

_LocalContentMixin._asm_ignorable_renderables += (naqchoices,
												  naqmlabels,
												  naqmvalues,
												  naqvalue,
												  naqchoice,
												  naqmlabel,
												  naqmvalue,
												  naqhints,
												  naqhint,
												  naqregex,
												  naqregexes,
												  naqwordentry,
												  naqwordbank,
												  naqordereditems,
												  naqordereditem)

class naqvideo(ntiincludevideo):
	blockType = True

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

class naquestion(_LocalContentMixin, Base.Environment, plastexids.NTIIDMixin):
	args = '[individual:str]'

	blockType = True

	# Only classes with counters can be labeled, and \label sets the
	# id property, which in turn is used as part of the NTIID
	# (when no NTIID is set explicitly)
	counter = 'naquestion'

	# Depending on the presence or absence of newlines
	# (and hence real paragraphs) within our top-level,
	# we either get children elements that are <par>
	# elements, or not. If they are <par> elements, the last
	# one contains the actual naqXXXpart children we are interested in.
	# If we set this to true, then we don't have that ambiguous
	# case; however, we wind up collecting too much content
	# into the `content` of the parts so we can't
	forcePars = False

	_ntiid_suffix = 'naq.'
	_ntiid_title_attr_name = 'ref'  # Use our counter to generate IDs if no ID is given
	_ntiid_allow_missing_title = True
	_ntiid_type = as_interfaces.NTIID_TYPE
	_ntiid_cache_map_name = '_naquestion_ntiid_map'

	def invoke( self, tex ):
		_t = super(naquestion,self).invoke(tex)
		if 'individual' in self.attributes and \
			self.attributes['individual'] == 'individual=true':
			self.attributes['individual'] = 'true'
		return _t

	@property
	def _ntiid_get_local_part(self):
		result = self.attributes.get( 'probnum' ) or self.attributes.get( "questionnum" )
		if not result:
			result = super(naquestion,self)._ntiid_get_local_part
		return result

	def _asm_videos(self):
		videos = []
		# video_els = self.getElementsByTagName( 'naqvideo' )
		# for video_el in video_els:
		#	videos.append( video_el._asm_local_content )

		return ''.join(videos)

	def _asm_question_parts(self):
		# See forcePars.
		# There may be a better way to make this determination.
		# naqassignment and the naquestionset don't suffer from this
		# issue because they can specifically ask for known child
		# nodes by name...we rely on convention
		to_iter = (x for x in self.allChildNodes
				   if hasattr(x, 'tagName') and x.tagName.startswith('naq') and x.tagName.endswith('part'))

		return [x.assessment_object() for x in to_iter if hasattr(x,'assessment_object')]

	def _createQuestion(self):
		result = question.QQuestion(content=self._asm_local_content,
									parts=self._asm_question_parts())
		return result

	@cachedIn('_v_assessment_object')
	def assessment_object(self):
		result = self._createQuestion()
		errors = schema.getValidationErrors( as_interfaces.IQuestion, result )
		if errors: # pragma: no cover
			raise errors[0][1]
		result.ntiid = self.ntiid # copy the id
		return result

class naquestionref(Crossref.ref):
	pass

class naquestionfillintheblankwordbank(naquestion, _WordBankMixIn):

	def _after_render(self, rendered):
		self._asm_local_content = _remove_parts_after_render(self, rendered)

	def _createQuestion(self):
		wordbank = self._asm_wordbank()
		result = question.QFillInTheBlankWithWordBankQuestion(content=self._asm_local_content,
															  parts=self._asm_question_parts(),
															  wordbank=wordbank)
		return result

@interface.implementer(crd_interfaces.IEmbeddedContainer)
class naquestionset(Base.List, plastexids.NTIIDMixin):
	r"""
	Question sets are a list of questions that should be submitted
	together. For authoring, questions are included in a question
	set by reference, and a question set can be composed of any
	other labeled questions found within the same processing unit.

	Example::

		\begin{naquestion}[individual=true]
			\label{question}
			...
		\end{question}

		\begin{naquestionset}<My Title>
			\label{set}
			\naquestionref{question}
		\end{naquestionset}

	"""

	args = "[options:dict:str] <title:str:source>"

	# Only classes with counters can be labeled, and \label sets the
	# id property, which in turn is used as part of the NTIID (when no NTIID is set explicitly)
	counter = 'naquestionset'

	_ntiid_suffix = 'naq.set.'
	_ntiid_title_attr_name = 'ref'  # Use our counter to generate IDs if no ID is given
	_ntiid_allow_missing_title = True
	_ntiid_type = as_interfaces.NTIID_TYPE
	_ntiid_cache_map_name = '_naquestionset_ntiid_map'

	#: From IEmbeddedContainer
	mimeType = "application/vnd.nextthought.naquestionset"

	@cachedIn('_v_assessment_object')
	def assessment_object(self):
		questions = [qref.idref['label'].assessment_object()
					 for qref in self.getElementsByTagName('naquestionref')]
		questions = PersistentList( questions )

		# Note that we may not actually have a renderer, depending on when
		# in our lifetime this is called (the renderer object mixin is deprecated
		# anyway)
		# If the title is ours, we're guaranteed it's a string. It's only in the
		# weird legacy code path that tries to inherit a title from some arbitrary
		# parent that it may not be a string
		if getattr(self, 'renderer', None) and not isinstance(self.title, six.string_types):
			title = text_type(''.join(render_children(getattr(self, 'renderer'),
													  self.title)))
		else:
			title = text_type(getattr(self.title, 'source', self.title))

		title = title.strip() or None

		result = question.QQuestionSet( questions=questions,
										title=title)
		errors = schema.getValidationErrors( as_interfaces.IQuestionSet, result )
		if errors: # pragma: no cover
			raise errors[0][1]
		result.ntiid = self.ntiid # copy the id
		return result

	@readproperty
	def question_count(self):
		return unicode(len(self.getElementsByTagName('naquestionref')))

	@readproperty
	def title(self):
		"""Provide an abstraction of the two ways to get a question set's title"""
		title = self.attributes.get('title') or None
		if title is None:
			# SAJ: This code path is bad and needs to go away
			title_el = self.parentNode
			while not hasattr(title_el, 'title'):
				title_el = title_el.parentNode
			title = title_el.title
		assert title is not None
		return title

###
# Assignments
###

class naquestionsetref(Crossref.ref):
	"A reference to the label of a question set."

	@readproperty
	def questionset(self):
		return self.idref['label']

class naassignmentpart(_LocalContentMixin,
					   Base.Environment):
	r"""
	One part of an assignment. These are always nested inside
	an :class:`naassignment` environment.

	Example::
		\begin{naquestionset}
			\label{set}
			\naquestionref{question}
		\end{naquestionset}

		\begin{naasignmentpart}[auto_grade=true]{set}
			Local content
		\end{naassignmentpart}

	"""

	args = "[options:dict:str] <title:str:source> question_set:idref"

	@cachedIn('_v_assessment_object')
	def assessment_object(self):
		question_set = self.idref['question_set'].assessment_object()
		return assignment.QAssignmentPart( content=self._asm_local_content,
										   question_set=question_set,
										   auto_grade=asbool(self.attributes.get('options',{}).get('auto_grade')),
										   title=self.attributes.get('title'))

class naassignment(_LocalContentMixin,
				   Base.Environment,
				   plastexids.NTIIDMixin):
	r"""
	Assignments specify some options such as availability dates,
	some local content, and finish up nesting the parts
	of the assignment as ``naassignmentpart`` elements.

	Example::

		\begin{naassignment}[not_before_date=2014-01-13,category=homework,public=true]<Homework>
			\label{assignment}
			Some introductory content.

			\begin{naasignmentpart}[auto_grade=true]{set}<Easy Part>
				Local content
			\end{naassignmentpart}
		\end{naquestionset}

	"""

	args = "[options:dict:str] <title:str:source>"

	# Only classes with counters can be labeled, and \label sets the
	# id property, which in turn is used as part of the NTIID (when no
	# NTIID is set explicitly)
	counter = 'naaassignment'
	_ntiid_cache_map_name = '_naassignment_ntiid_map'
	_ntiid_allow_missing_title = True
	_ntiid_suffix = 'naq.asg.'
	_ntiid_title_attr_name = 'ref' # Use our counter to generate IDs if no ID is given
	_ntiid_type = as_interfaces.NTIID_TYPE

	@cachedIn('_v_assessment_object')
	def assessment_object(self):
		# FIXME: We want these to be relative, not absolute, so they
		# can be made absolute based on when the course begins.
		# How to represent that? Probably need some schema transformation
		# step in nti.externalization? Or some auixilliary data fields?
		options = self.attributes.get('options') or ()
		def _parse(key, default_time):
			if key in options:
				val = options[key]
				if 'T' not in val:
					val += default_time

				# Now parse it, assuming that any missing timezone should be treated
				# as local timezone
				dt = datetime_from_string(
							val,
							assume_local=True,
							local_tzname=self.ownerDocument.userdata.get('document_timezone_name'))
				return dt

		# If they give no timestamp, make it midnight
		not_before = _parse('not_before_date', 'T00:00')
		# For after, if they gave us no time, make it just before
		# midnight. Together, this has the effect of intuitively defining
		# the range of dates as "the first instant of before to the last minute of after"
		not_after = _parse('not_after_date', 'T23:59')

		# Public/ForCredit.
		# It's opt-in for authoring and opt-out for code
		is_non_public = True
		if 'public' in options and asbool(options['public']):
			is_non_public = False

		result = assignment.QAssignment(
						content=self._asm_local_content,
						available_for_submission_beginning=not_before,
						available_for_submission_ending=not_after,
						parts=[part.assessment_object() for part in
							   self.getElementsByTagName('naassignmentpart')],
						title=self.attributes.get('title'),
						is_non_public=is_non_public)
		if 'category' in options:
			result.category_name = \
				as_interfaces.IQAssignment['category_name'].fromUnicode( options['category'] )

		errors = schema.getValidationErrors( as_interfaces.IQAssignment, result )
		if errors: # pragma: no cover
			raise errors[0][1]

		result.ntiid = self.ntiid
		return result

def ProcessOptions( options, document ):
	# We are not setting up any global state here,
	# only making changes to the document, so its
	# fine that this runs each time we are imported
	document.context.newcounter('naquestion')
	document.context.newcounter('naassignment')
	document.context.newcounter('naquestionset')
	document.context.newcounter('naqsolutionnum')
	document.context.newcounter('naquestionfillintheblankwordbank')

#: The directory in which to find our templates.
#: Used by plasTeX because we implement IPythonPackage
template_directory = os.path.abspath( os.path.dirname(__file__) )

#: The directory containing our style files
texinputs_directory = os.path.abspath( os.path.dirname(__file__) )

interface.moduleProvides(IOptionAwarePythonPackage)
