import httplib2
import logging
import os
import pickle

from apiclient.discovery import build
from oauth2client.appengine import oauth2decorator_from_clientsecrets
from oauth2client.client import AccessTokenRefreshError
from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

MISSING_CLIENT_SECRETS_MESSAGE = """
<h1>Warning: Please configure OAuth 2.0</h1>
<p>
To make this sample run you will need to populate the client_secrets.json file
found at:
</p>
<p>
<code>%s</code>.
</p>
<p>with information found on the <a
href="https://code.google.com/apis/console">APIs Console</a>.
</p>
""" % CLIENT_SECRETS


http = httplib2.Http(memcache)
#http = httplib2.Http()
service = build("calendar", "v3", http=http)
decorator = oauth2decorator_from_clientsecrets(
    CLIENT_SECRETS,
    'https://www.googleapis.com/auth/calendar',
    MISSING_CLIENT_SECRETS_MESSAGE)

class MainHandler(webapp.RequestHandler):

    path = os.path.join(os.path.dirname(__file__), 'index.html')
    
    @decorator.oauth_aware
    def get(self):
        #variables = dict(url=decorator.authorize_url(), has_credentials=decorator.has_credentials())
        variables = ''
        content = template.render(self.path, variables)
        self.response.out.write(content)


def get_events(http):
    events = service.events().list(calendarId='primary').execute(http)
    events_list = []
    while True:
        for event in events['items']:
            events_list.append(event['summary'])
            page_token = events.get('nextPageToken')
            if page_token:
                events = service.events().list(calendarId='primary', pageToken=page_token).execute(http)
            else:
                break
    return events_list


class AboutHandler(webapp.RequestHandler):

    path = os.path.join(os.path.dirname(__file__), 'index.html')
    
    @decorator.oauth_required
    def get(self):
        try:
            http = decorator.http()
            events = get_event(http)
            context = dict(events=events)
            content = template.render(path, context)
            self.response.out.write(content)
        except AccessTokenRefreshError:
            logging.error('!!!')
            self.redirect('/')


def main():
    application = webapp.WSGIApplication(
      [
       ('/', MainHandler),
       ('/about', AboutHandler),
      ],
      debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
    main()
