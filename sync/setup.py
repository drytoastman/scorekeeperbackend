from setuptools import setup, find_packages

x = setup(
    name='synclogic',
    version='2.0',
    description='Scorekeeper Database Synchronization',
    author='Brett Wilson',
    author_email='N/A',
    url='https://github.com/drytoastman/ScorekeeperBackend',
    install_requires=[
        "sccommon",
    ],
    dependency_links=[
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [ 'syncserver = synclogic:main' ]
    },
    include_package_data=True,
    zip_safe=False,
)
