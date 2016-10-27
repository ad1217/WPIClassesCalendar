# WPI Classes Calendar #
This script uses a username and password for BannerWeb (`bannerweb.wpi.edu`) to scrape the student's schedule and produce an iCal `.ics` file. It is written to run on a web server using Flask.

It might also be useful as an example on how to log into BannerWeb programatically.

## Requirements ##
  * pytz
  * icalendar
  * requests
  * BeautifulSoup
  * Flask

## Installation ##
You will need a `preferences.py` with contents:
```
SID = "YOUR_USERNAME"
PIN = "YOUR_PASSWORD"
```
where `YOUR_USERNAME` and `YOUR_PASSWORD` are replaced with your username and password, respectively.
