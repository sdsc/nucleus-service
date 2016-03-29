# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages

from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md')) as f:
    long_description = f.read()

with open('requirements.txt') as reqs:
    install_requires = [
        line for line in reqs.read().split('\n') if (line and not
                                                     line.startswith('--'))
    ]

setup(
    name='nucleus_service',
    version=__import__('nucleus_service').__version__,
    author='Dmitry Mishin',
    author_email='dmishin@sdsc.edu',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['README.md'],
    },
    url='https://github.com/sdsc/nucleus',
    license='Apache-2.0',
    description='Package description',
    long_description=long_description,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
    ],
    zip_safe=False,
    install_requires=install_requires,
)
