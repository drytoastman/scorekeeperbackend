from setuptools import setup, find_packages
setup(
    name='nwrsc',
    version='2.0',
    description='Scorekeeper Web Service',
    author='Brett Wilson',
    author_email='N/A',
    url='https://github.com/drytoastman/ScorekeeperBackend',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[ "sccommon" ],
    scripts=['bin/webserver.py', 'bin/assets_preload.py'],
)
