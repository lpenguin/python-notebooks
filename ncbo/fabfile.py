__author__ = 'nikitaprianichnikov'

from fabric.api import *
from fabric.operations import *
from fabric.contrib.files import exists
from fabric.contrib.project import *
from fabric.decorators import roles


host = 'ec2-user@52.3.130.45'
env.hosts = [host]

def update():
    rsync_project(remote_dir='.',
              exclude=[
                  '.idea/',
                  '.DS_Store',
                  '.git/',
                  '.gitignore',
                  '__pycache__',
                  '*.pid',
                  '*.pyc',
                  '.R*',
                  'affy/',
                  'packrat/',
              ])
