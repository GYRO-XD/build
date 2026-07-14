from setuptools import setup, find_packages
from Cython.Build import cythonize
import os

setup(
    name="gyro-secure",
    version="1.0.0",
    description="Advanced Greyhat Security Testing Framework",
    author="GYRO-XD",
    packages=find_packages(),
    ext_modules=cythonize(
        "gyro_secure.py",
        compiler_directives={
            'language_level': 3,
            'boundscheck': False,
            'wraparound': False,
        }
    ),
    install_requires=[
        'requests>=2.28.0',
        'beautifulsoup4>=4.11.0',
        'rich>=13.0.0',
        'python-whois>=0.7.0',
        'dnspython>=2.3.0',
        'urllib3>=1.26.0',
    ],
    entry_points={
        'console_scripts': [
            'gyro=gyro_secure:main',
        ],
    },
    zip_safe=False,
)
