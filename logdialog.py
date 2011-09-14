# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from sqlobject import AND

from jinja2 import Template

from yokadi.db import Task

from ui_logdialog import Ui_LogDialog

TEMPLATE = Template(u"""
<html>
<head>
<style>
body {
    font-family: sans-serif;
}
h1 {
    font-size: 140%;
    text-align: center;
}
h2 {
    font-size: 120%;
    margin: 0;
    padding: 0;
    padding-top: 1em;
}
h2:first-child {
    padding-top: 0;
}
ul {
    margin: 0;
}
.day {
    border-top: 1px dotted silver;
}
.day:first-child {
    border-top: none;
}
</style>
</head>
<body>
{% for date, projects in dct|dictsort %}
    <div class='day'>
    <h1>{{ date.strftime("%A %d %B %Y") }}</h1>
    {% for project, tasks in projects|dictsort %}
        <h2>{{ project }}</h2>
        <ul>
        {% for task in tasks %}
            <li>{{ task }}</li>
        {% endfor %}
        </ul>
    {% endfor %}
    </div>
{% endfor %}
</tr>
</table>
</body>
</html>
""")

def datetimeFromQDate(qdate):
    return datetime(qdate.year(), qdate.month(), qdate.day())

class LogDialog(QDialog):
    def __init__(self):
        super(LogDialog, self).__init__()
        self.ui = Ui_LogDialog()
        self.ui.setupUi(self)
        self.layout().setMargin(0)

        self.ui.fromDateEdit.setFocus()
        self.ui.fromDateEdit.setDate(QDate.currentDate())
        self.ui.toDateEdit.setDate(QDate.currentDate())

        self.ui.webView.settings().setDefaultTextEncoding("utf-8")

        QObject.connect(self.ui.fromDateEdit, SIGNAL("dateChanged(QDate)"), self.updateView)
        QObject.connect(self.ui.toDateEdit, SIGNAL("dateChanged(QDate)"), self.updateView)

        self.updateView()

    def updateView(self):
        minDate = datetimeFromQDate(self.ui.fromDateEdit.date())
        maxDate = datetimeFromQDate(self.ui.toDateEdit.date())
        if maxDate < minDate:
            minDate, maxDate = maxDate, minDate

        maxDate += timedelta(1)
        tasks = Task.select(AND( \
            Task.q.status == "done", \
            Task.q.doneDate >= minDate, \
            Task.q.doneDate < maxDate, \
            ))

        # Create a tree-like struct with a dict of the form:
        # {date => {project => [tasks]}
        # Ie:
        # date1
        # - project1
        #   - foo
        #   - bar
        # - project2
        #   - baz
        dct = {}
        for task in tasks:
            date = task.doneDate.date()
            project = task.project.name
            title = task.title

            if not date in dct:
                dct[date] = {}
            if not project in dct[date]:
                dct[date][project] = []

            dct[date][project].append(title)

        # Add missing days
        date = minDate.date()
        while date < maxDate.date():
            if not date in dct:
                dct[date] = {}
            date += timedelta(1)

        html = TEMPLATE.render(dct=dct)
        self.ui.webView.setHtml(html)
