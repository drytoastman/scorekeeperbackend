from setuptools import setup, find_packages

x = setup(
    name='synclogic',
    version='2.0',
    description='Scorekeeper Database Synchronization',
    author='Brett Wilson',
    author_email='N/A',
    url='https://github.com/drytoastman/ScorekeeperBackend',
    install_requires=[],
    packages=find_packages(),
    scripts=['bin/syncserver.py'],
    include_package_data=True,
    zip_safe=False,
)

