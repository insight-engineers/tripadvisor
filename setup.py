from setuptools import setup, find_packages

setup(
    name="tripadvisor",
    version="0.1.0",
    packages=find_packages(include=["tripadvisor", "tripadvisor.*"]),
)
