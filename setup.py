from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))


with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='peg',
    version='0.1.dev0',
    description='PEG parsing library',
    long_description=long_description,
    url='https://github.com/ethframe/peg',
    author='ethframe',
    license='MIT',
    packages=find_packages(exclude=['examples']),
)
