from setuptools import setup, find_packages

setup(
    name='libs',  # The name of your library
    version='0.1',
    packages=find_packages(where='libs'),  # Tells setuptools where to find the libraries
    package_dir={'': 'libs'},  # Tells where the package is located
)
setup()