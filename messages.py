#!/usr/bin/python2.6
"""Threaded IRC client with plugin support (vaguely)."""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '0.5'

# Standard modules
import datetime
import re

# Custom modules
import errors

# Notices
SERVER_NOTICE = re.compile(':(?:[^@]+?) NOTICE ([#\w]+?) :(.*)')
USER_NOTICE = re.compile(':(.*?@.*?) NOTICE .*? :(.*)')

# Channel/private message parsing
MESSAGE_REGULAR = re.compile(':(.*?) PRIVMSG (.*?) :(.*)')
IDENT_SPLIT = re.compile('(.+?)!(.+?)@(.*)')

# Server messages
SERVER_GENERAL = re.compile(':.*? (\d{3}) ([\w*]+?) (.*)')
SERVER_PING = re.compile('PING :(.*)')
SERVER_MODE = re.compile(':(.*?) MODE (\w+?) (.*)')
SERVER_JOIN = re.compile(':(.*?) JOIN :(.*)')
SERVER_PART = re.compile(':(.*?) PART (.*)')
SERVER_ERROR = re.compile('ERROR :(.*)')

# General server message codes, guessed meanings and display fixes
SERVER_MESSAGE_CODES = {
    1: lambda msg: ('WELCOME', msg[1:]),
    2: lambda msg: ('SERVER HOST', msg[1:]),
    3: lambda msg: ('CREATION', msg[1:]),
    4: lambda msg: ('SERVER VERSION', msg),
    5: lambda msg: ('CAPABILITIES', msg.split(' :')[0]),
    42: lambda msg: ('UNIQUE ID', msg.split(' :')[0]),
    251: lambda msg: ('USERS', msg[1:]),
    252: lambda msg: ('OPERATORS', msg.split(' :')[0]),
    254: lambda msg: ('CHANNELS', msg.split(' :')[0]),
    255: lambda msg: ('USERS', msg[1:]),
    265: lambda msg: ('USERS', msg[1:]),
    266: lambda msg: ('USERS', msg[1:]),
    353: lambda msg: ('NAMES', ': '.join(msg[2:].split(' :'))),
    366: lambda msg: ('NAMES', ': '.join(msg.split(' :'))),
    372: lambda msg: ('MOTD', msg[1:]),
    375: lambda msg: ('MOTD', msg[1:]),
    376: lambda msg: ('MOTD', msg[1:]),
    396: lambda msg: ('DISPLAYED HOST', msg.split(' :')[0]),
    433: lambda msg: ('NICK', ': '.join(msg.split(' :'))),
    }

# ##############################################################################
# Message classes (for incoming messages)
#
class Message(object):
  def __init__(self, content):
    self.timestamp = datetime.datetime.now()
    self.content = content

  def __repr__(self):
    attrs = ', '.join('%s=%r' % item for item in vars(self).iteritems())
    return '%s(%s)' % (type(self).__name__, attrs)


class ServerMessage(Message):
  pass


class Join(ServerMessage, Message):
  def __init__(self, ident, content):
    super(Join, self).__init__(content)
    self.nick, self.user, self.host = IDENT_SPLIT.match(ident).groups()

  def __str__(self):
    return '[%s] JOIN %s BY %s' % (
        self.timestamp.strftime('%T'), self.content, self.nick)


class Part(ServerMessage, Message):
  def __init__(self, ident, content):
    super(Part, self).__init__(content)
    self.nick, self.user, self.host = IDENT_SPLIT.match(ident).groups()

  def __str__(self):
    return '[%s] PART %s BY %s' % (
        self.timestamp.strftime('%T'), self.content, self.nick)


class Ping(ServerMessage, Message):
  def __str__(self):
    return '[%s] PING %s' % (
        self.timestamp.strftime('%T'), self.content)


class Error(ServerMessage, Message):
  def __str__(self):
    raise errors.ConnectionError("ERROR: Server terminated connection (%s)"
                                 % self.content)


class Mode(ServerMessage, Message):
  def __init__(self, ident, channel, content):
    super(Mode, self).__init__(content)
    self.ident = ident
    self.channel = channel

  def __str__(self):
    return '[%s] MODE %s %s' % (
        self.timestamp.strftime('%T'), self.channel, self.content)


class ServerGeneral(ServerMessage, Message):
  def __init__(self, code, recipient, content):
    default = lambda msg: ('UNKNOWN', msg)
    name, content = SERVER_MESSAGE_CODES.get(int(code), default)(content)
    super(ServerGeneral, self).__init__(content)
    self.code = int(code)
    self.name = name
    self.recipient = recipient

  def __str__(self):
    return '[%s] SERVER [%03d %s]: %s' % (
      self.timestamp.strftime('%T'), self.code, self.name, self.content)


class ServerNotice(ServerMessage, Message):
  def __init__(self, scope, content):
    super(ServerNotice, self).__init__(content)
    self.scope = scope

  def __str__(self):
    return '[%s] SERVERNOTICE <%s>: %s' % (
        self.timestamp.strftime('%T'), self.scope, self.content)


class UserNotice(Message):
  def __init__(self, ident, content):
    super(UserNotice, self).__init__(content)
    self.nick, self.user, self.host = IDENT_SPLIT.match(ident).groups()

  def __str__(self):
    return '[%s] NOTICE <%s>: %s' % (
        self.timestamp.strftime('%T'), self.nick, self.content)


class PrivateMessage(Message):
  def __init__(self, ident, channel, content):
    super(PrivateMessage, self).__init__(content)
    self.nick, self.user, self.host = IDENT_SPLIT.match(ident).groups()
    self.channel = channel
    self.content = content

  def Ident(self):
    return '%s!%s@%s' % (self.nick, self.user, self.host)

  def __repr__(self):
    return '%s(ident=%r, channel=%r, content=%r)' % (
        type(self).__name__, self.Ident(), self.channel, self.content)


class ChannelMessage(PrivateMessage):
  """Messages received inside a channel."""
  def __str__(self):
    return '[%s] %s <%s>: %s' % (
        self.timestamp.strftime('%T'),
        self.channel, self.nick, self.content)


class QueryMessage(PrivateMessage):
  """Messages sent by another user in a QUERY."""
  def __str__(self):
    return '[%s] QUERY <%s>: %s' % (self.timestamp.strftime('%T'),
                              self.nick, self.content)


def ParseMessage(message):
  """Returns the appropriate message class for the received raw message."""
  if MESSAGE_REGULAR.match(message):
    return ParsePrivateMessage(message)
  elif 'NOTICE' in message:
    return ParseNotice(message)
  return ParseServerMessage(message)


def ParseNotice(message):
  """Returns a proper Notice type message."""
  if SERVER_NOTICE.match(message):
    return ServerNotice(*SERVER_NOTICE.match(message).groups())
  return UserNotice(*USER_NOTICE.match(message).groups())


def ParsePrivateMessage(message):
  """Parses a private message and returns either a channel or query message."""
  ident, channel, content = MESSAGE_REGULAR.match(message).groups()
  if channel.startswith('#'):
    return ChannelMessage(ident, channel, content)
  return QueryMessage(ident, channel, content)


def ParseServerMessage(message):
  """Parses a server message and returns the appropriate message class."""
  if SERVER_PING.match(message):
    return Ping(*SERVER_PING.match(message).groups())
  elif SERVER_GENERAL.match(message):
    return ServerGeneral(*SERVER_GENERAL.match(message).groups())
  elif SERVER_MODE.match(message):
    return Mode(*SERVER_MODE.match(message).groups())
  elif SERVER_JOIN.match(message):
    return Join(*SERVER_JOIN.match(message).groups())
  elif SERVER_PART.match(message):
    return Part(*SERVER_PART.match(message).groups())
  elif SERVER_ERROR.match(message):
    return Error(*SERVER_ERROR.match(message).groups())
  return ServerMessage(message)
