from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyso-builder",
    version="1.0.0",
    author="GYRO-XD",
    author_email="gyro.xd@proton.me",
    description="Professional Python to .so Compiler Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GYRO-XD/pyso-builder",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
    ],
    python_requires=">=3.8",
    install_requires=[
        "cython>=0.29.0",
        "setuptools>=45.0.0",
    ],
    entry_points={
        "console_scripts": [
            "pyso=pyso_builder:main",
        ],
    },
)
