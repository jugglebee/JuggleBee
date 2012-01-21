#!/usr/bin/env python

import base64
import cgi
import hashlib
import json
import logging
import os
import urllib2

from google.appengine.api import users
from google.appengine.api import urlfetch

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from google.appengine.ext import db

from mycalendar import Calendar
#from service import service

calendar = Calendar()


class User(db.Model):
  username= db.StringProperty()
  email = db.StringProperty()
  date = db.DateTimeProperty(auto_now_add=True)


def user_key(user_type=None):
  return db.Key.from_path('User', user_type or 'default_user')


def authenticate():
    user = users.get_current_user()
    if user and users.is_current_user_admin():
        return (('user', user.nickname()), 
                ('logout_url', users.create_logout_url('/')))
    else:
        return (('login_url', users.create_login_url('/')),)


class MainHandler(webapp.RequestHandler):

    path = os.path.join(os.path.dirname(__file__), 'index.html')

    def get(self):
        context = dict(authenticate())
        content = template.render(self.path, context)
        self.response.out.write(content)

    def post(self):
        username = self.request.get('username')
        email = self.request.get('email')
        user_type = 'user'
        user_new = User(parent=user_key(user_type))
        user_new.username = username
        user_new.email = email
        user_new.put()
        logging.info('%s - %s' % (username, email))
        context = dict(authenticate(), username=username, email=email, thanks="Thank you for your subscription!")
        content = template.render(self.path, context)
        self.response.out.write(content)


class DetailHandler(webapp.RequestHandler):

    path = os.path.join(os.path.dirname(__file__), 'page.html')

    def get(self):
        context = dict(authenticate())
        content = template.render(self.path, context)
        self.response.out.write(content)

def parse_feed(feed):

    entries = [unicode(e.title.text) for e in feed.entry]
    return entries    

def show_feed(feed):
    logging.debug(unicode(feed.title.text))
    logging.debug(unicode(feed.entry))
    for e in feed.entry:
        logging.debug(unicode(e.title.text))

class CommandHandler(webapp.RequestHandler):

    def post(self):
        logging.debug('CommandHandler!')
        logging.debug(cgi.escape(self.request.get("command")))
        feed = calendar.get_calendars()
        content = json.dumps(dict(result=parse_feed(feed)))
        logging.debug(content)
        self.response.headers['Content-Type'] ='application/json'
        self.response.out.write(content)


class UserHandler(webapp.RequestHandler):
    
    def post(self):
        user_type = self.request.get('user_type')
        user_new = User(parent=user_key(user_type))
        user_new.username = users.get_current_user()
        user_new.description = self.request.get('user_description')
        user_new.put()
        content = json.dumps(dict(result='Added user has been!'))
        self.response.headers['Content-Type'] ='application/json'
        self.response.out.write(content)

    def get(self):
        user_type = 'user'
        user_list = db.GqlQuery("SELECT * "
                                "FROM User "
                                "WHERE ANCESTOR IS :1 "
                                "ORDER BY date DESC LIMIT 10",
                                user_key(user_type))
        content = unicode([unicode(i.username+'-'+i.email) for i in user_list])
        self.response.out.write(content)

def decode_signed_req(data):
    data += "=" * (len(data) - 4)
    data = json.loads(base64.urlsafe_b64decode(data))
    return data

def csrf_protection(signature, payload):
    if not signature == hashlib.sha256(payload).hexdigest():
        logging.debug(signature)
        logging.error('Cross Site Request Forgery might have occured')

def get_graph(token):
    address = "https://graph.facebook.com/me?access_token=%s" % token
    graph = json.loads(urllib2.urlopen(address).read())
    logging.debug(graph)
    return graph

def get_events():
    events = service.events().list(calendarId='primary').execute()
    events_list = []
    while True:
        for event in events['items']:
            events_list.append(event['summary'])
            page_token = events.get('nextPageToken')
            if page_token:
                events = service.events().list(calendarId='primary', pageToken=page_token).execute()
            else:
                break
    return events_list

class FacebookHandler(webapp.RequestHandler):

    path = os.path.join(os.path.dirname(__file__), 'index.html')

    def post(self):
        post_data = cgi.FieldStorage()
        signature, payload = post_data['signed_request'].value.split('.',1)
        csrf_protection(signature, payload)
        payload = decode_signed_req(payload)
        graph = get_graph(payload['oauth_token'])
        events = get_events()
        logging.info(payload)
        context = dict(token=payload, events=events, graph=graph)
        content = template.render(self.path, context)
        self.response.out.write(content)


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    application = webapp.WSGIApplication([('/', MainHandler), 
                                          ('/command', CommandHandler),
                                          ('/detail', DetailHandler),
                                          ('/facebook/', FacebookHandler),
                                          ('/user', UserHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
