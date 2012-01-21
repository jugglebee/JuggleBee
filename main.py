#!/usr/bin/env python

import base64
import cgi
import hashlib
import json
import logging
import os
import urllib2

import gdata

from google.appengine.api import users
from google.appengine.api import urlfetch

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from google.appengine.ext import db

from mycalendar import Calendar

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


def get_calendars(self, own=False):

    if own:
        feed = self.client.GetOwnCalendarsFeed()
    else:
        feed = self.client.GetAllCalendarsFeed()
    return feed



def get_events():

    feed = calendar.client.GetCalendarEventFeed()
    events = []
    events.append(feed.title.text)

    try: 
        debug = str(feed.entry[0].__dict__)
    except IndexError:
        debug = 'No matching results found.'

    for evt in feed.entry:
        d = {}
        d['title'] = evt.title.text
        d['participants'] = []
        for p in evt.who:
            status = p.email
            if p.attendee_status:
                status += p.attendee.status.value
            d['participants'].append(status)
        events.append(d)
    return debug, events

def get_events_by_date(start_date='2012-01-20', end_date='2012-01-21'):
    
    #query = gdata.calendar.client.CalendarEventQuery(text_query='Sabrosa')
    query = gdata.calendar.client.CalendarEventQuery()
    query.start_min = start_date
    query.start_max = end_date
    feed = calendar.client.GetCalendarEventFeed(q=query)
    
    events = []
    events.append(feed.title.text)

    try:
        debug = str(feed.entry[0].__dict__)
    except IndexError:
        debug = 'No matching results found.'

    for evt in feed.entry:
        d = {}
        d['title'] = evt.title.text
        d['when'] = []
        for when in evt.when:
            d['when'].append(when.start+' - '+when.end)
        events.append(d)

    return debug, events

class CoursesHandler(webapp.RequestHandler):

    path = os.path.join(os.path.dirname(__file__), 'course.html')

    def get(self):
        debug, events = get_events()
        context = dict(authenticate(), courses=events, debug=debug, logout_url='/')
        content = template.render(self.path, context)
        self.response.out.write(content)



class CalendarHandler(webapp.RequestHandler):

    path = os.path.join(os.path.dirname(__file__), 'calendar2.html')

    def get(self):
        debug, events = get_events_by_date()
        context = dict(authenticate(), events=events, debug=debug)
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

    def get(self):
        logging.debug('CommandHandler!')
        logging.debug(cgi.escape(self.request.get("command")))
        feed = calendar.get_calendars()
        content = json.dumps(dict(result=parse_feed(feed)))
        logging.debug(content)
        self.response.headers['Content-Type'] ='application/json'
        self.response.out.write(content)

class PresentationHandler(webapp.RequestHandler):

    path = os.path.join(os.path.dirname(__file__), 'presentation.html')
    
    def get(self):
        content = template.render(self.path, dict())
        self.response.out.write(content)

class AttendeeHandler(webapp.RequestHandler):

    path = os.path.join(os.path.dirname(__file__), 'attendee.html')
    
    def get(self):
        content = template.render(self.path, dict(attendees=''))
        self.response.out.write(content)


class AttendeeCreateHandler(webapp.RequestHandler):

    path = os.path.join(os.path.dirname(__file__), 'attendee_create.html')
    
    def get(self):
        content = template.render(self.path, dict())
        self.response.out.write(content)


class AttendeeViewHandler(webapp.RequestHandler):

    path = os.path.join(os.path.dirname(__file__), 'attendee_view.html')
    
    def get(self):
        content = template.render(self.path, dict())
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
        content = str([str(i.username+'-'+i.email) for i in user_list])
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

class FacebookHandler(webapp.RequestHandler):

    path = os.path.join(os.path.dirname(__file__), 'calendar.html')

    def post(self):
        post_data = cgi.FieldStorage()
        signature, payload = post_data['signed_request'].value.split('.',1)
        csrf_protection(signature, payload)
        payload = decode_signed_req(payload)
        graph = get_graph(payload['oauth_token'])
        debug, events = get_events()
        logging.info(payload)
        context = dict(token=payload, events=events, graph=graph)
        content = template.render(self.path, context)
        self.response.out.write(content)


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/atd', AttendeeHandler), 
                                          ('/atdcreate', AttendeeCreateHandler), 
                                          ('/atdview', AttendeeViewHandler), 
                                          ('/presentation', PresentationHandler), 
                                          ('/command', CommandHandler),
                                          ('/calendar', CalendarHandler),
                                          ('/courses', CoursesHandler),
                                          ('/facebook/', FacebookHandler),
                                          ('/user', UserHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
