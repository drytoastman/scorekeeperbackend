from setuptools import setup, find_packages
setup(
    name='mailman',
    version='2.0',
    description='Scorekeeper Email Processing',
    author='Brett Wilson',
    author_email='N/A',
    url='https://github.com/drytoastman/ScorekeeperBackend',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[ "sccommon" ],
    entry_points={ 'console_scripts': [ 'mailman = mailman:main' ] },
)
