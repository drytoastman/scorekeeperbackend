from setuptools import setup, find_packages

x = setup(
    name='mailman',
    version='2.0',
    description='Scorekeeper Email Processing',
    author='Brett Wilson',
    author_email='N/A',
    url='https://github.com/drytoastman/ScorekeeperBackend',
    install_requires=[],
    packages=find_packages(),
    scripts=['bin/mailman.py'],
    include_package_data=True,
    zip_safe=False,
)

