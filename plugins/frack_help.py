#!/usr/bin/python
"""help plugin for IRC bot."""
__author__ = 'Martijn Berntsen <mxberntsen@gmail.com>'
__version__ = '0.1'

# Standard modules
import urllib2
import threading
import time
import simplejson
import re
from datetime import datetime, date

# Custom modules
import messages
import plugins

# Static values
TRIGGER = "!help"
MSG = "[\x02Nomz\x02] %s"

# Below value is to tell the monitor to use the local TCP proxy or listen to the
# UDP port (spaceannounce protocol) directly.
PROXY = True
# Set to TRUE if the bot is NOT running within the space network.
HTTP = False

class Plugin(plugins.Base):
  """Prints the message to the console."""
  def __init__(self):
    self.thread = None
  
  def CanHandle(self, message):
    """ Returns the messages it can handle. """
    return (isinstance(message, messages.ChannelMessage)
            and message.content.startswith(TRIGGER))

  def Process(self, server, message):
    server.SendMessage(message.channel, '/me houdt %ss handje vast' % (message.nick), None)
      

