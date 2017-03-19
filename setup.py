from setuptools import setup, find_packages
import os

PROJECT_DIR = os.path.dirname(__file__)


def get_requirements(filename):
    with open(filename) as fp:
        return [
            requirement
            for requirement in fp
            if requirement and not requirement.startswith('#')
        ]

setup(
    name='scrapy-twostage',
    version='0.0.1',
    packages=find_packages(),
    url='http://github.com/acordiner/scrapy-twostage',
    license='GPL v2',
    author='Alister Cordiner',
    author_email='alister@cordiner.net',
    description='Use S3 as a cache backend in Scrapy projects.',
    long_description=open(os.path.join(PROJECT_DIR, 'README.rst')).read(),
    install_requires=get_requirements(os.path.join(PROJECT_DIR, 'requirements.txt')),
    test_suite='tests',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
)