#!/usr/bin/env python3
import time
from datetime import datetime, timedelta
from icalendar import Calendar, Event
from preferences import *
import requests
from bs4 import BeautifulSoup

urls = {'home'         : "https://bannerweb.wpi.edu/pls/prod/twbkwbis.P_WWWLogin",
        'login'        : "https://bannerweb.wpi.edu/pls/prod/twbkwbis.P_ValLogin",
        'logout'       : "https://bannerweb.wpi.edu/pls/prod/twbkwbis.P_Logout",
        'main_menu'    : "https://bannerweb.wpi.edu/pls/prod/twbkwbis.P_GenMenu?name=bmenu.P_MainMnu",
        'registration' : "https://bannerweb.wpi.edu/pls/prod/twbkwbis.P_GenMenu?name=bmenu.P_RegMnu",
        'select_term'  : "https://bannerweb.wpi.edu/pls/prod/bwcklibs.P_StoreTerm",
        'view_classes' : "https://bannerweb.wpi.edu/pls/prod/bwskfshd.P_CrseSchdDetl",
        'view_term'    : "https://bannerweb.wpi.edu/pls/prod/bwskflib.P_SelDefTerm"}

def login():
    s = None
    login_success = False
    while not login_success:
        s = requests.Session()
        s.get(urls["home"])
        r = s.get(urls["login"], params={"sid": SID, "PIN": PIN})
        login_success = (r.status_code == 200)
        if not login_success:
            print("Login failed, retrying")
            time.sleep(5)
    return s

def get_classes(s):
    s.get(urls["view_term"], headers={'referer': urls["registration"]})
    #soup = BeautifulSoup(r.text, 'html.parser')
    #soup.find(id="term_id").children
    term = "201602" #make dynamic eventually
    r= s.get(urls['select_term'], params={'term_in': term})
    r = s.get(urls['view_classes'])
    return r

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

                class_data = {'title'            : caption[0],
                              'course'           : caption[1],
                              'section'          : caption[2],
                              'CRN'              : class_col[1].text,
                              'status'           : class_col[2].text,
                              'class_instructor' : class_col[3].text.replace('\n', ''),
                              'times'            : time_col[1].text.split(" - "),
                              'days'             : time_col[2].text,
                              'location'         : time_col[3].text,
                              'dates'            : time_col[4].text.split(" - "),
                              'type'             : time_col[5].text,
                              'instructor'       : time_col[6].text}
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

def generate_calendar(classes):
    cal = Calendar()
    cal.add('prodid', '-//WPI Calender Generator//adamgoldsmith.name//')
    cal.add('version', '2.0')

    for c in classes:
        event = Event()
        # push the start and end dates back one day, then exclude the start date
        # this fixes a problem where the first day of the term would have all of the classes
        start_date = datetime.strptime(c['dates'][0] + " " + c['times'][0], "%b %d, %Y %I:%M %p") - timedelta(days=1)
        end_date = datetime.strptime(c['dates'][0] + " " + c['times'][1], "%b %d, %Y %I:%M %p") - timedelta(days=1)
        final_end_date = datetime.strptime(c["dates"][1], "%b %d, %Y")
        event.add('summary', c['course'] + " " + c['type'])
        event.add('dtstart', start_date)
        event.add('location', c['location'])
        event.add('description', c['title'] + " " + c['section'])
        event.add('dtend', end_date)
        event.add('rrule', {'freq': "weekly", 'until': final_end_date, 'byday': format_days(c['days'])})
        event.add('exdate', start_date)
        event.add('dtstamp', datetime.now())

        cal.add_component(event)
    return cal

def main():
    session = login()
    resp = get_classes(session)
    class_list = parse_classes(resp)
    calendar = generate_calendar(class_list)

    with open('example.ics', 'wb') as f:
        f.write(calendar.to_ical())

    session.get(urls["logout"])
    session.close()

main()
