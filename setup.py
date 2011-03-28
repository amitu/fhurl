from setuptools import setup, find_packages

setup(
    name = "fhurl",
    version = "0.1.0",
    url = 'http://github.com/amitu/fhurl',
    license = 'BSD',
    description = "Django generic form handler view",
    long_description = file("README.rst").read(),
    author = 'Amit Upadhyay',
    author_email = "upadhyay@gmail.com",
    py_modules = ["fhurl"],
)
