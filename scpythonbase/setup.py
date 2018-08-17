from setuptools import setup, find_packages

x = setup(
    name='sccommon',
    version='2.0',
    description='Scorekeeper Python Common Base',
    author='Brett Wilson',
    author_email='N/A',
    install_requires=[
        'pytz',
        'psycopg2==2.7.5'
    ],
    packages=find_packages(),
    zip_safe=False,
)

