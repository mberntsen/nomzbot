#!/usr/bin/python
"""Spacenomz planning plugin for IRC bot."""
__author__ = 'Martijn Berntsen <mxberntsen@gmail.com>'
__version__ = '0.1'

# Standard modules
import urllib2
import threading
import time
import simplejson
import re
from datetime import datetime, date
import copy

# Custom modules
import messages
import plugins

# Static values
TRIGGER = "!nomz"
MSG = "[\x02Nomz\x02] %s"
days = ['maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag']
DAY_NAME_TO_NUMBER = {'maandag':0, 'dinsdag':1, 'woensdag':2, 'donderdag':3, 'vrijdag':4, 'zaterdag':5, 'zondag':6}
DAY_NUMBER_TO_NAME = {0:'maandag', 1:'dinsdag', 2:'woensdag', 3:'donderdag', 4:'vrijdag', 5:'zaterdag', 6:'zondag'}
USER_ADD = re.compile('^\+([0-9]+)(?: (maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|vandaag))?$')
USER_REMOVE = re.compile('^-([0-9]+)(?: (maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|vandaag))?$')

# Below value is to tell the monitor to use the local TCP proxy or listen to the
# UDP port (spaceannounce protocol) directly.
PROXY = True
# Set to TRUE if the bot is NOT running within the space network.
HTTP = False

class Plugin(plugins.Base):
  """Prints the message to the console."""
  def __init__(self):
    self.thread = None
    self.date = datetime.today().date()
    self.loadSchedule()
    self.loadToday()
  
  def loadSchedule(self):
    f = open('schedule.json', 'r')
    self.schedule = simplejson.load(f)
    f.close()

  def saveSchedule(self):
    f = open('schedule.json', 'w')
    s = {}
    for day in days:
      s[day] = self.schedule[day]
    simplejson.dump(s, f)
    f.close()

  def loadToday(self, server=None):
    self.schedule['vandaag'] = copy.deepcopy(self.schedule[DAY_NUMBER_TO_NAME[self.date.weekday()]])
    if server is not None:
      server.SendMessage('#avondeten', 'whoa, nieuwe dag, nieuwe eters!', None)

  def addUser(self, nick, server, quantity, day=None):
    if day is None:
      day = 'vandaag'
    quantity = int(quantity)
    if quantity <= 0:
      return False
    isFound = False
    print day
    for user in self.schedule[day]:
      if user['nick'] == nick:
        isFound = True
        user['quantity'] += quantity
        break
    if not isFound:
      user = {'nick': nick, 'quantity': quantity}
      self.schedule[day].append(user)
    if day != 'vandaag':
      self.saveSchedule()
    server.SendMessage('#avondeten', 'je staat voor %s met %d personen op de planning' % (day, user['quantity']), nick)

  def removeUser(self, nick, server, quantity, day=None):
    if day is None:
      day = 'vandaag'
    quantity = int(quantity)
    if quantity <= 0:
      return False
    isFound = False
    print day
    for user in self.schedule[day]:
      if user['nick'] == nick:
        isFound = True
        user['quantity'] -= quantity
        if user['quantity'] == 0:
          self.schedule[day].remove(user)
          server.SendMessage('#avondeten', 'je staat voor %s niet meer op de planning' % day, nick)
        else:
          server.SendMessage('#avondeten', 'je staat voor %s  met %d personen op de planning' % (day, user['quantity']), nick)
        break
    if day != 'vandaag':
      self.saveSchedule()
    if not isFound:
      server.SendMessage('#avondeten', 'je stond niet op de lijst van %s' % day, nick)

  def CanHandle(self, message):
    """ Returns the messages it can handle. """
    return (isinstance(message, messages.ChannelMessage)
            and (USER_ADD.match(message.content)
              or USER_REMOVE.match(message.content)
              or message.content == 'wie'
              or message.content == 'wat'
              or message.content == 'planning'
              or (('help' in message.content) and ('nomzbot' in message.content))))

  def Process(self, server, message):
    if self.date < datetime.today().date():
        self.date = datetime.today().date()
        self.loadToday()
          
    if USER_ADD.match(message.content):
      self.addUser(message.nick, server, *USER_ADD.match(message.content).groups())
    elif USER_REMOVE.match(message.content):
      print repr(USER_REMOVE.match(message.content).groups())
      self.removeUser(message.nick, server, *USER_REMOVE.match(message.content).groups())
    elif message.content == 'nieuwedag':
      self.loadToday(server)
    elif message.content == 'wie':
      wiestring = ''       
      totaal = 0
      for user in self.schedule['vandaag']:
        if len(wiestring) > 0:
          wiestring = wiestring + ', '
        if user['quantity'] == 1:
          wiestring = wiestring + '%s' % user['nick']
        else:
          wiestring = wiestring + '%s (%dx)' % (user['nick'], user['quantity'])
        totaal = totaal + user['quantity']
      if totaal == 0:
        server.SendMessage(message.channel, 'er eten geen mensen mee', message.nick)
      else:
        server.SendMessage(message.channel, 'er eten %d mensen mee, te weten: %s' % (totaal, wiestring), message.nick)
    elif message.content == 'planning':
      for day in days:
        wiestring = ''       
        totaal = 0
        for user in self.schedule[day]:
          if len(wiestring) > 0:
            wiestring = wiestring + ', '
          if user['quantity'] == 1:
            wiestring = wiestring + '%s' % user['nick']
          else:
            wiestring = wiestring + '%s (%dx)' % (user['nick'], user['quantity'])
          totaal = totaal + user['quantity']
        if totaal == 0:
          server.SendMessage(message.channel, '%-9s: niemand' % day, message.nick)
        else:
          server.SendMessage(message.channel, '%-9s: er eten %d mensen mee, te weten: %s' % (day, totaal, wiestring), message.nick)
    elif message.content == 'wat':
      request = urllib2.Request('http://www.receptenvandaag.nl/random')
      opener = urllib2.build_opener()
      f = opener.open(request)
      server.SendMessage(message.channel, 'wat dacht je van: %s' % f.url, message.nick)
    elif (('help' in message.content) and ('nomzbot' in message.content)):
      server.SendMessage(message.channel, 'aanmelden/afmelden voor vandaag: +1/-1', None)
      server.SendMessage(message.channel, 'voor vaste dagen, dag toevoegen (bijv dinsdag): +1/-1 dinsdag', None)
      server.SendMessage(message.channel, 'vaste eters bekijken: planning', None)
      server.SendMessage(message.channel, 'wie eten er vandaag mee?: wie', None)
      server.SendMessage(message.channel, 'wat eten we vandaag?: wat', None)
    

