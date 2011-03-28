from fabric.api import local

def docs():
    local("./bin/docs")
    local("./bin/python setup.py upload_sphinx --upload-dir=docs/html")
