#!/usr/bin/python2.6
"""Core server messages plugin for IRC bot."""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '0.1'

# Custom modules
import messages
import plugins


class Plugin(plugins.Base):
  def CanHandle(self, message):
    return isinstance(message, messages.ServerMessage)

  def Process(self, server, message):
    if isinstance(message, messages.Ping):
      server.SendCommand('PONG', message.content)

    if isinstance(message, messages.ServerNotice):
      if message.scope == 'Auth' and not server.identified:
        server.nickname = server.config['nick']
        server.server_socket.send('USER %s\r\n' % server.identity)
        server.server_socket.send('NICK %s\r\n' % server.nickname)
        server.identified = True

    if isinstance(message, messages.ServerGeneral):
      if message.code == 1:
        print 'releasing Semaphore'
        server.available.release()
      if message.code == 433:
        server.nickname += "_"
        server.server_socket.send('NICK %s\r\n' % server.nickname)
