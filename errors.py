#!/usr/bin/python2.6
"""Custom error class to be able to generate errors without having a callback
in every plugin or module. """
__author__ = 'Rudi Daemen <fludizz@gmail.com>'
__version__ = '0.1'

class ConnectionError(Exception):
  pass
    
class SendError(Exception):
  pass
