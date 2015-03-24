import os
from pip.req import parse_requirements
from setuptools import setup
import re

install_reqs = parse_requirements('requirements.txt')
install_requires = []
dependency_links = []
for ir in install_reqs:
    install_requires.append(str(ir.req))
    if ir.url:
        url = re.sub(r'^-e ', '', str(ir.url))
        dependency_links.append(str(url))

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "openfilter_twitter",
    version = "0.1",
    author = "Martin Quiroga",
    author_email = "martin@quiroga.co",
    description = ("OpenFilter for Twitter."),
    license = "Private",
    url = "http://pypi.openfilter.co/openfilter_twitter",
    packages=['openfilter_twitter'],
    scripts=['initDB.py', 'record.py', 'twitterBuffer.py'],
    long_description=read('README.md'),
    classifiers=[ ],
    install_requires=install_requires,
    dependency_links=dependency_links,
)
