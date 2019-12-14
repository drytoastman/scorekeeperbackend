from setuptools import setup, find_packages
setup(
    name='scdns',
    version='2.0',
    description='Scorekeeper Nameserver',
    author='Brett Wilson',
    author_email='N/A',
    url='https://github.com/drytoastman/ScorekeeperBackend',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={ 'console_scripts': [ 'dnsserver = scdns:main', ]},
)
