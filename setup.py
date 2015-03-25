from setuptools import setup
import platform

version = '0.0.1'
packages = [
        'quickbase',
        ]
install_requires = [
        'setuptools',
        'BeautifulSoup4 >= 4.0.0',
        'lxml',
        ]

setup(
    name='py-quickbase',
    version=version,
    packages=packages,
    license='MasTec proprietary',
    url='http://www.mastec.com/',
    author='Bob Uhl',
    author_email='robert.uhl@mastec.com',
    install_requires=install_requires,
    )
