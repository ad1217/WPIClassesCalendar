#!/usr/bin/env python3
import time
from datetime import datetime, timedelta
import pytz
import icalendar
from preferences import *
import requests
from bs4 import BeautifulSoup
from flask import Flask

app = Flask(__name__)

urls = {'home'         : "https://bannerweb.wpi.edu/pls/prod/twbkwbis.P_WWWLogin",
        'login'        : "https://bannerweb.wpi.edu/pls/prod/twbkwbis.P_ValLogin",
        'logout'       : "https://bannerweb.wpi.edu/pls/prod/twbkwbis.P_Logout",
        'main_menu'    : "https://bannerweb.wpi.edu/pls/prod/twbkwbis.P_GenMenu?name=bmenu.P_MainMnu",
        'registration' : "https://bannerweb.wpi.edu/pls/prod/twbkwbis.P_GenMenu?name=bmenu.P_RegMnu",
        'select_term'  : "https://bannerweb.wpi.edu/pls/prod/bwcklibs.P_StoreTerm",
        'view_classes' : "https://bannerweb.wpi.edu/pls/prod/bwskfshd.P_CrseSchdDetl",
        'view_term'    : "https://bannerweb.wpi.edu/pls/prod/bwskflib.P_SelDefTerm"}


def setup_session():
    s = requests.Session()
    s.get(urls["home"])
    r = s.get(urls["login"], params={"sid": SID, "PIN": PIN}, headers={'referer': urls["login"]})
    if not r.status_code == 200:
        print("Login failed")
        exit(1)

    return s

def get_classes(s, term):
    s.get(urls["view_term"], headers={'referer': urls["registration"]})
    s.get(urls['select_term'], params={'term_in': term}, headers={'referer': urls["view_term"]})
    r = s.get(urls['view_classes'], headers={'referer': urls["registration"]})

    if not r.status_code == 200:
        print("Login failed")
        exit(1)

    return r

def close_session(s):
    s.get(urls["logout"])
    s.close()

def parse_classes(r):
    classes = []
    soup = BeautifulSoup(r.text, 'html.parser')
    tables = soup.find_all(attrs={'class':"datadisplaytable"})
    for index, class_table in enumerate(tables):
        if class_table.caption.text == "Scheduled Meeting Times":
            continue
        else:
            class_col = class_table.find_all(attrs={'class':"dddefault"})
            caption = class_table.caption.text.split(' - ')
            for row in tables[index + 1].find_all('tr'):
                time_col = row.find_all('td', attrs={'class':"dddefault"})
                if time_col == []:
                    continue

                class_data = {'title'             : caption[0],
                              'course'            : caption[1],
                              'section'           : caption[2],
                              'CRN'               : class_col[1].text,
                              'status'            : class_col[2].text,
                              'course_instructor' : class_col[3].text.replace('\n', ''),
                              'times'             : time_col[1].text.split(" - "),
                              'days'              : time_col[2].text,
                              'location'          : time_col[3].text,
                              'dates'             : time_col[4].text.split(" - "),
                              'type'              : time_col[5].text,
                              'instructor'        : time_col[6].text.replace(" (P)", ""),
                              'instructor_email'  : time_col[6].a.get("href") if time_col[6].a is not None else None}
                classes.append(class_data)
    return classes

def format_days(days):
    day_map = {"S": "SU",
               "M": "MO",
               "T": "TU",
               "W": "WE",
               "R": "TH",
               "F": "FR",
               "?": "SA"} #Hmmm. I don't have any examples of this or Sunday
    return [day_map[d] for d in days]

def format_dates(date, time=None):
    date_fmt = "%b %d, %Y"
    time_fmt = "%I:%M %p"
    if time is not None:
        date = datetime.strptime(date + time, date_fmt + time_fmt)
    else:
        date = datetime.strptime(date, date_fmt)
    return pytz.timezone('US/Eastern').localize(date).astimezone(pytz.utc)

def generate_calendar(classes):
    cal = icalendar.Calendar()
    cal.add('prodid', '-//WPI Calender Generator//adamgoldsmith.name//')
    cal.add('version', '2.0')

    for index, c in enumerate(classes):
        event = icalendar.Event()
        # push the start and end dates back one day, then exclude the start date
        # this fixes a problem where the first day of the term would have all of the classes
        start_date = format_dates(c['dates'][0], c['times'][0]) - timedelta(days=1) # start of the first class
        end_date = format_dates(c['dates'][0], c['times'][1]) - timedelta(days=1) # end of the first class
        final_end_date = format_dates(c["dates"][1]) # end of the term
        event.add('summary', c['course'] + " " + c['type'])
        event.add('dtstart', start_date)
        event.add('location', c['location'])
        event.add('description', "{0} {1}\n{2} {3}".format(c['title'], c['section'], c['instructor'], c['instructor_email']))
        event.add('dtend', end_date)
        event.add('rrule', {'freq': "weekly", 'until': final_end_date, 'byday': format_days(c['days'])})
        event.add('exdate', start_date)
        event.add('uid', "WPICal" + str(index) + "@adamgoldsmith.name")
        event.add('dtstamp', datetime.now())

        if c['instructor_email'] is not None:
            organizer = icalendar.vCalAddress(c['instructor_email'])
            organizer.params['cn'] = c['instructor']
            event['organizer'] = organizer

        alarm = icalendar.Alarm()
        alarm.add('trigger', icalendar.vDuration(timedelta(minutes=-10)))
        alarm.add('action', "display")
        event.add_component(alarm)

        cal.add_component(event)
    return cal

@app.route("/")
def main():
    class_list = []
    year = str((datetime.now() + timedelta(weeks=26)).year)
    terms = [year + "01", year + "02", year + "03"]
    session = setup_session()
    for term in terms:
        resp = get_classes(session, term)
        class_list += parse_classes(resp)
        resp = get_classes(session, term)

    close_session(session)
    return generate_calendar(class_list).to_ical()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
