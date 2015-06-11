import codecs
from setuptools import setup, find_packages

VERSION = '0.0.0'

entry_points = {
	"z3c.autoinclude.plugin": [
		'target = nti.contentrendering',
	],
	"console_scripts": [
		"nti_extract_assessments = nti.assessment.scripts.nti_task_policy_extractor:main"
	],
}

TESTS_REQUIRE = [
	'nose',
	'nose-timer',
	'nose-pudb',
	'nose-progressive',
	'nose2[coverage_plugin]',
	'pyhamcrest',
	'nti.testing'
]

setup(
	name='nti.assessment',
	version=VERSION,
	author='Jason Madden',
	author_email='jason@nextthought.com',
	description="Support for automated assessments",
	long_description=codecs.open('README.rst', encoding='utf-8').read(),
	license='Proprietary',
	keywords='Assessments',
	classifiers=[
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: Implementation :: CPython'
	],
	packages=find_packages('src'),
	package_dir={'': 'src'},
	namespace_packages=['nti', ],
	tests_require=TESTS_REQUIRE,
	install_requires=[
		'setuptools',
 		'persistent',
 		'dolmen.builtins',
 		'persistent',
 		'plone.namedfile',
 		'repoze.lru',
 		'simplejson',
 		'six',
 		'sympy',
 		'zope.annotation',
 		'zope.app.file',
 		'zope.component',
 		'zope.container',
 		'zope.deferredimport',
 		'zope.dublincore',
 		'zope.interface',
 		'zope.datetime',
 		'zope.file',
 		'zope.location',
 		'zope.mimetype',
 		'zope.schema',
 		'zope.security',
 		'nti.common',
 		'nti.contentfragments',
 		'nti.coremetadata',
 		'nti.dataserver_core',
 		'nti.dataserver_fragments',
 		'nti.dublincore',
 		'nti.externalization',
 		'nti.mimetype',
 		'nti.namedfile',
 		'nti.openmath',
 		'nti.plasTeX',
 		'nti.schema'
	],
	extras_require={
		'test': TESTS_REQUIRE,
	},
	dependency_links=[],
	entry_points=entry_points
)
