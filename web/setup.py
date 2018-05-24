from setuptools import setup, find_packages

x = setup(
    name='nwrsc',
    version='2.0',
    description='Scorekeeper Web Service',
    author='Brett Wilson',
    author_email='N/A',
    url='https://github.com/drytoastman/wwscc',

    install_requires=[
        "Flask",
        "Flask-Assets",
        "Flask-Bcrypt",
        "Flask-Compress",
        "Flask-Mail",
        "Flask-Markdown",
        "Flask-Sockets",
        "Flask-WTF",
        "cheroot",
        "icalendar",
        "libsass",
        "ReportLab",
        "paypalrestsdk",
        "psycopg2",
        "python-dateutil",
        "squareconnect"
    ],

    dependency_links = [
        "git+https://github.com/drytoastman/connect-python-sdk.git@master#egg=squareconnect"
    ],

    packages=find_packages(),
    scripts=['bin/webserver.py', 'bin/assets_preload.py'],
    include_package_data=True,
    zip_safe=False,
)

