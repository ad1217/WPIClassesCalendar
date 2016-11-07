#!/usr/bin/env python3
import sys
import os
from flask import Flask

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import WPIClassesCalendar

app = Flask(__name__)

@app.route("/")
def main():
    return WPIClassesCalendar.main()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
