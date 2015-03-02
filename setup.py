import codecs
from setuptools import setup, find_packages

VERSION = '0.0.0'

entry_points = {
	"z3c.autoinclude.plugin": [
		'target = nti.contentrendering',
	],
}

TESTS_REQUIRE = [
	'nose',
	'nose-timer',
	'nose-pudb',
	'nose-progressive',
	'nose2[coverage_plugin]',
	'pyhamcrest',
	'nti.nose_traceback_info',
	'nti.testing'
]

setup(
	name = 'nti.assessment',
	version = VERSION,
	author = 'Jason Madden',
	author_email = 'jason@nextthought.com',
	description = "Support for automated assessments",
	long_description = codecs.open('README.rst', encoding='utf-8').read(),
	license = 'Proprietary',
	keywords = 'Assessments',
	classifiers = [
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: Implementation :: CPython'
	],
	packages=find_packages('src'),
	package_dir={'': 'src'},
	namespace_packages=['nti',],
	tests_require=TESTS_REQUIRE,
	install_requires=[
		'setuptools',
		'persistent',
		'pytz',
		'dolmen.builtins',
		'dm.zope.schema',
		'persistent',
		'plone.namedfile',
		'repoze.lru',
		'simplejson',
		'six',
		'sympy',
		'zope.annotation',
		'zope.app.file',
		'zope.cachedescriptors',
		'zope.component',
		'zope.container',
		'zope.dublincore',
		'zope.interface',
		'zope.datetime',
		'zope.file',
		'zope.location',
		'zope.mimetype',
		'zope.schema',
		'nti.common',
		'nti.contentfragments',
		'nti.coremetadata',
		'nti.dataserver.core',
		'nti.dataserver.fragments',
		'nti.dublincore',
		'nti.externalization',
		'nti.links',
		'nti.ntiids',
		'nti.openmath',
		'nti.plasTeX',
		'nti.schema'
	],
	extras_require={
		'test': TESTS_REQUIRE,
	},
	dependency_links=[
		'git+https://github.com/NextThought/nti.schema.git#egg=nti.schema',
		'git+https://github.com/NextThought/nti.nose_traceback_info.git#egg=nti.nose_traceback_info'
	],
	entry_points=entry_points
)
