from setuptools import setup, find_packages

x = setup(
    name='mailman',
    version='2.0',
    description='Scorekeeper Email Processing',
    author='Brett Wilson',
    author_email='N/A',
    url='https://github.com/drytoastman/ScorekeeperBackend',
    install_requires=[
        "sccommon",
        "beautifulsoup4==4.6.0",
        "lxml==3.7.3"
    ],
    dependency_links=[
    ],
    entry_points={
        'console_scripts': [ 'mailman = mailman:main' ]
    },
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)

