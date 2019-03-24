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
    entry_points={ 'console_scripts': [
                    'crondaemon = sccommon.cronjobs:crondaemon',
                    'restoredb  = sccommon.backuprestore:restorecmd',
                    'backupdb   = sccommon.backuprestore:backupcmd'
                ]},
)
