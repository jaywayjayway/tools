from setuptools import setup, find_packages

setup(
    name="domainctl",
    version="0.1",
    scripts=[
        'bin/domainctl',
    ],
    description="domainctl",
    packages=find_packages(),
)
