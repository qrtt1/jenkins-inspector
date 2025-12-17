"""Setup script for jenkins-inspector"""

from setuptools import setup, find_packages

# For backward compatibility with older build tools
# Modern builds should use pyproject.toml
setup(
    packages=find_packages(),
)
