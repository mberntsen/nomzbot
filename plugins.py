#!/usr/bin/python2.6
"""Threaded IRC client with plugin support (vaguely)."""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '0.1'

# Standard modules
import imp
import os

PLUGIN_DIRECTORY = os.path.join(os.path.dirname(__file__), 'plugins')


class Base(object):
  """A plugin has a single process method that handles on a received message."""
  def CanHandle(self, message):
    """Returns whether the plugin can handle the given message class."""
    raise NotImplementedError

  def Process(self, server, message):
    """Plugin acts according to received message."""
    raise NotImplementedError


def LoadPluginByName(name):
  """Returns a plugin instance based on its name and with the given conn."""
  module_info = imp.find_module(name, [PLUGIN_DIRECTORY])
  module = imp.load_module('bot_plugin_%s' % name, *module_info)
  print 'Loading plugin: %r' % name
  return module.Plugin()


def LoadPlugins():
  """Yields all plugins in the 'plugins' dir, instantiated with given conn."""
  for plugin in sorted(os.listdir(PLUGIN_DIRECTORY)):
    name, extension = os.path.splitext(plugin)
    if extension == '.py':
      yield LoadPluginByName(name)
