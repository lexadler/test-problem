from setuptools import PEP420PackageFinder
from setuptools import setup

setup(
    name='treeview',
    install_requires=list(open('requirements.txt').read().split()),
    packages=PEP420PackageFinder.find(
        include=['treeview', 'treeview.*']
    ),
    entry_points={
        'console_scripts': [
            'treeview = treeview.__main__:main',
        ]
    },
    options={
        'check': {'metadata': True, 'strict': True, },
    },
)
