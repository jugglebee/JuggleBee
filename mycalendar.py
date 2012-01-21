import atom
import getopt
import sys
import string
import time

import gdata.calendar.data
import gdata.calendar.client
import gdata.acl.data

from xml.etree import ElementTree

class Calendar:

    def __init__(self, email='medicine.django', password='9NtyW8_a'):
        
        source = 'Test Python Client'
        self.client =  gdata.calendar.client.CalendarClient(source)
        self.client.ClientLogin(email, password, self.client.source)


    def get_calendars(self, own=False):
        
        if own:
            feed = self.client.GetOwnCalendarsFeed()
        else:
            feed = self.client.GetAllCalendarsFeed()
        return feed
    
    def query_event(self, text='', date_start='', date_stop=''):
        if text:
            query = gdata.calendar.client.CalendarEventQuery(text=text)
        elif date_start and date_stop:
            query = gdata.calendar.client.CalendarEventQuery(start_min=date_start, start_max=date_start)
        
        feed = self.client.GetCalendarEventFeed(q=query)
        return feed


    def insert_calendar(self, title='Simple Scheduler.', description='', location='',
        time_zone='', hidden=False, color='#2952A3'):
        
        calendar = gdata.calendar.data.CalendarEntry()
        calendar.title = atom.data.Title(text=title)
        calendar.summary = atom.data.Summary(text=description)
        calendar.where.append(gdata.calendar.data.CalendarWhere(value=location))
        calendar.color = gdata.calendar.data.ColorProperty(value=color)
        calendar.timezone = gdata.calendar.data.TimeZoneProperty(value=time_zone)

        if hidden:
            calendar.hidden = gdata.calendar.data.HiddenProperty(value='true')
        else:
            calendar.hidden = gdata.calendar.data.HiddenProperty(value='false')

        new_calendar = self.client.InsertCalendar(new_calendar=calendar)
        return new_calendar

    def update_calendar(self):
        pass

    def delete_calendars(self):
        pass

    def insert_event(self, title='Simple event.', content='Simple event description.', 
        where='Wherever.', start_time=None, end_time=None, recurrence_data=None):
        event = gdata.calendar.data.CalendarEventEntry()
        event.title = atom.data.Title(text=title)
        event.content = atom.data.Content(text=content)
        event.where.append(gdata.data.Where(value=where))

        if recurrence_data is not None:
            # Set a recurring event
            event.recurrence = gdata.data.Recurrence(text=recurrence_data)
        
        elif start_time is None:
            # Use current time for the start_time and have the event last 1 hour
            start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
            end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z',
                time.gmtime(time.time() + 3600))
        event.when.append(gdata.data.When(start=start_time, end=end_time))

        new_event = self.client.InsertEvent(event)
        return new_event

if __name__ == '__main__':
    c = Calendar()
    feed = c.get_calendars()
    print feed.title.text
    print feed.entry[0]
    #for f in feed.entry:
    #    print f
