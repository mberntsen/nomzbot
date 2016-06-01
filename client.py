#!/usr/bin/python2.6
"""Threaded IRC client with plugin support (vaguely)."""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '0.5'

# Standard modules
import socket
import threading
import time

# Custom modules
import messages
import plugins
import errors

IDENT = '%s * * :%s'


class Client(object):
  def __init__(self, nick, realname=None, channel='frack_devel'):
    self.plugins = list(plugins.LoadPlugins())
    self.servers = []

    self.channel = channel
    self.nick = nick
    self.realname = realname or nick

  def Connect(self, server, port=6667):
    config = {'client': self,
              'host': (server, port),
              'nick': self.nick,
              'realname': self.realname,
              'channel': self.channel}
    server_conn = ServerConnection(config)
    self.servers.append(server_conn)
    return server_conn

  def LoadPlugin(self, plugin_name):
    """Adds a plugin to the IRC connection/client."""
    self.plugins.append(plugins.LoadPluginByName(plugin_name))


# ##############################################################################
# Actual IRC server thread. (this needs a ton of cleanup)
#
class ServerConnection(threading.Thread):
  """IRC client in a thread, allowing asynchronous handling of messages."""
  def __init__(self, config):
    super(ServerConnection, self).__init__(name=self.__class__.__name__)
    self.daemon = True
    # Actual client configuration
    self.config = config
    self.channel = self.config['channel']
    self.nickname = self.config['nick']
    self.client = self.config['client']
    self.realname = self.config['realname']
    self.host = self.config['host']
    self.identity = IDENT % (self.nickname, self.realname)
    self.identified = False
    self.Connect()
    self.start()

  def run(self):
    """Forever running loop, which starts when we're connected."""
    prev_msg = ''
    reconnect = False
    while True:
      try:
        prev_msg = self.ProcessIncoming(prev_msg)
        if self.identified and reconnect:
        # This is a dirty way to rejoin a channel but it works!
        # NEEDS FIXING!!!
          threading.Timer(10, self.JoinChannel).start()
          reconnect = False
      except (socket.error, errors.ConnectionError), err:
        print 'Connection failed (%s). Retrying...' % err
        self.Connect()
        reconnect = True

  def Connect(self):
    print 'Connecting to IRC server'
    connected = False
    self.identified = False
    self.available = threading.Semaphore(0)
    #try:
    #  self.server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    #except socket.error:
    self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server_socket.settimeout(600)
    while not connected:
      try:
        self.server_socket.connect(self.host)
        connected = True
      except socket.error:
        print 'Connection failed, retry...'
        time.sleep(5)

  def ProcessIncoming(self, remainder):
    """Reads lines from the incoming socket and delegates them to be handled.

    Incomplete lines are returned as a remainder, which is prefixed to the next
    chunk of content read from the socket.
    """
    chunk = remainder + (self.server_socket.recv(1024) or '')
    lines = chunk.split('\r\n')
    for line in lines[:-1]:
      self.HandleMessage(messages.ParseMessage(line))
    return lines[-1]

  def HandleMessage(self, message):
    """We received a message, run it past all plugins!"""
    for plugin in self.client.plugins:
      if plugin.CanHandle(message):
        plugin.Process(self, message)

  def SendRaw(self, message):
    """Sends a raw message to the server, adding newline at the end.

    N.B. A small pause is inserted after sending a message to prevent floods.
    """
    if isinstance(message, unicode):
      message = message.encode('utf-8')
    with self.available:
      print '>>> %s' % message
      try:
        self.server_socket.send(message + '\r\n')
      except Exception, err:
        print "Failed to send message (%s)" % err
        raise errors.ConnectionError("Failed to send message (%s)" % err)
      time.sleep(0.1)

  # ############################################################################
  # All sorts of actual IRC commands
  #
  def JoinChannel(self, channel=None):
    """Joins a channel, name needs not have a leading hash."""
    self.channel = channel or self.channel
    self.SendRaw('JOIN %s' % ChannelName(self.channel))

  def SetNick(self, nickname):
    """Sets the nickname of the client."""
    self.SendRaw('NICK %s' % nickname)
    self.nickname = nickname

  def SetUserMode(self, mode):
    """Updates usermodes."""
    self.SendRaw('MODE %s %s' % (self.nickname, mode))

  def SetChannelMode(self, channel, mode):
    """Updates channel modes if allowed."""
    self.SendRaw('MODE %s %s' % (ChannelName(channel), mode))

  def SendCommand(self, command, content):
    """Sends a command with a string argument to the server."""
    self.SendRaw('%s %s' % (command, content))

  def SendMessage(self, recipient, message, address=None):
    """Sends a message to a channel or user."""
    if address:
      message = '%s, %s' % (address, message)
    self.SendRaw('PRIVMSG %s :%s' % (recipient, message))


def ChannelName(channel):
  """Returns a proper channel name, with a single leading hash tag."""
  return '#%s' % channel.lstrip('#')
