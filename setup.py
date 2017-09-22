import codecs
from setuptools import setup, find_packages

entry_points = {
    "z3c.autoinclude.plugin": [
        'target = nti.contentrendering',
    ],
    "console_scripts": [
        "nti_extract_assessments = nti.assessment.scripts.nti_task_policy_extractor:main"
    ],
}


TESTS_REQUIRE = [
    'nti.testing',
    'zope.dottedname',
    'zope.testrunner',
]


def _read(fname):
    with codecs.open(fname, encoding='utf-8') as f:
        return f.read()


setup(
    name='nti.assessment',
    version=_read('version.txt').strip(),
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="Support for automated assessments",
    long_description=(_read('README.rst') + '\n\n' + _read('CHANGES.rst')),
    license='Apache',
    keywords='assessment',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        "Framework :: assessment",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    url="https://github.com/NextThought/nti.assessment",
    zip_safe=True,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['nti'],
    tests_require=TESTS_REQUIRE,
    install_requires=[
        'setuptools',
        'persistent',
        'nti.base',
        'nti.contentfragments',
        'nti.contenttypes.reports',
        'nti.coremetadata',
        'nti.dublincore',
        'nti.externalization',
        'nti.mimetype',
        'nti.namedfile',
        'nti.ntiids',
        'nti.openmath',
        'nti.plasTeX',
        'nti.property',
        'nti.publishing',
        'nti.recorder',
        'nti.schema',
        'nti.wref',
        'persistent',
        'repoze.lru',
        'requests',
        'simplejson',
        'six',
        'sympy',
        'zope.annotation',
        'zope.component',
        'zope.container',
        'zope.deferredimport',
        'zope.dublincore',
        'zope.interface',
        'zope.datetime',
        'zope.file',
        'zope.location',
        'zope.mimetype',
        'zope.proxy',
        'zope.schema',
        'zope.security'
    ],
    extras_require={
        'test': TESTS_REQUIRE,
        'docs': [
            'Sphinx',
            'repoze.sphinx.autointerface',
            'sphinx_rtd_theme',
        ],
    },
    entry_points=entry_points,
)
