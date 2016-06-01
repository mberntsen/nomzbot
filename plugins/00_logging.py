#!/usr/bin/python2.6
"""Logging plugin for IRC bot."""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '0.1'

# Custom modules
import plugins


class Plugin(plugins.Base):
  """Prints the message to the console."""
  def CanHandle(self, message):
    return True

  def Process(self, server, message):
    print message
