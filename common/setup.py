from setuptools import setup, find_packages
setup(
    name='sccommon',
    version='2.0',
    description='Scorekeeper Python Common',
    author='Brett Wilson',
    author_email='N/A',
    url='https://github.com/drytoastman/ScorekeeperBackend',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    scripts=['bin/cloudbackup.py', 'bin/cronjobs.py']
)
