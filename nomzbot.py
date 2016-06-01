#!/usr/bin/python
"""IRC Bot connector."""
__author__ = 'Elmer de Looff <elmer@underdark.nl>'
__version__ = '0.2'

# Standard modules
import sys
import time
import optparse

# Custom modules
import client

# Change these defaults to fit your bot if you're copying this plx
NICKNAME = 'nomzbot'
REALNAME = 'nomzbot - http://frack.nl/wiki/FrackBot'
CHANNEL = '#avondeten'
SERVER = 'irc.eth-0.nl'

def ConnectToServer(nick=NICKNAME, real=REALNAME, chan=CHANNEL, server=SERVER):
  """Connect to server and channel."""
  irc = client.Client(nick, real, chan)
  server = irc.Connect(server)
  server.JoinChannel()
  while True:
    # To keep things from shutting down prematurely
    try:
      time.sleep(1)
    except KeyboardInterrupt:
      sys.exit('\nBye, it\'s been fun!')


if __name__ == '__main__':
  usage = "usage: %prog [options]"
  parser = optparse.OptionParser(usage=usage)
  parser.add_option("-n", "--nick", metavar="NICKNAME", default=NICKNAME,
                    help="The nickname the bot should use.")
  parser.add_option("-r", "--realname", metavar="REALNAME", default=REALNAME,
                    help="The nickname the bot should use.")
  parser.add_option("-c", "--channel", metavar="CHANNEL", default=CHANNEL,
                    help="The channel it should join.")
  parser.add_option("-s", "--server", metavar="SERVER", default=SERVER,
                    help="The IRC Server it should connect to.")
  (opts, args) = parser.parse_args()
  try:
    print "%s: unrecognized argument \'%s\'" % (sys.argv[0], args[0])
    print "usage: %s [options]\r\nTry \'%s --help\' for more information." % (
          sys.argv[0], sys.argv[0])
    sys.exit(0)
  except IndexError:
    pass
  print "Using nickname \'%s\' (\'%s\') in channel \'%s\' on server \'%s\'." % (
         opts.nick, opts.realname, opts.channel, opts.server)
  ConnectToServer(opts.nick, opts.realname, opts.channel, opts.server)

