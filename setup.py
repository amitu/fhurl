from setuptools import setup

setup(
    name = "fhurl",
    version = "0.1.10",
    url = 'http://packages.python.org/fhurl/',
    license = 'BSD',
    description = "Django generic form handler view",
    author = 'Amit Upadhyay',
    author_email = "upadhyay@gmail.com",
    install_requires = ["smarturls"],
    py_modules = ["fhurl"],
)
