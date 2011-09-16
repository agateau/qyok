# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from sqlobject import AND, LIKE, IN
from sqlobject.sqlbuilder import Select

from jinja2 import Environment

from yokadi.db import Task, Project

from ui_logdialog import Ui_LogDialog

def formatdate(date):
    """
    strftime may return a string with accent ("August" in fr is "Août" for
    example), so we need to turn it into proper unicode.
    """
    return unicode(date.strftime("%A %d %B %Y"), "utf-8")

ENVIRONMENT = Environment()
ENVIRONMENT.filters["formatdate"] = formatdate
TEMPLATE = ENVIRONMENT.from_string(u"""
<html>
<head>
<style>
body {
    font-family: sans-serif;
    background-color: #bbb;
    padding: 0;
    margin: 0;
}
h1 {
    font-size: 120%;
    text-align: center;
    padding: 0;
    margin: 0;
}
h2 {
    font-size: 100%;
    margin: 0;
    padding: 0;
    padding-top: 0.5em;
}
h2:first-child {
    padding-top: 0;
}
ul {
    margin: 0;
    padding: 0;
    padding-left: 1.5em;
}
li {
    margin: 0;
}
.day {
    border: 1px solid #444;
    margin: 6px;
    padding: 6px;
    background-color: white;
}
</style>
</head>
<body>
{% for date, projects in dct|dictsort|reverse %}
    <div class='day'>
    <h1>{{ date|formatdate }}</h1>
    {% for project, tasks in projects|dictsort %}
        <h2>{{ project|e }}</h2>
        <ul>
        {% for task in tasks %}
            <li>{{ task|e }}</li>
        {% endfor %}
        </ul>
    {% endfor %}
    </div>
{% endfor %}
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
        QObject.connect(self.ui.projectLineEdit, SIGNAL("textChanged(QString)"), self.updateView)
        QObject.connect(self.ui.showEmptyDaysCheckBox, SIGNAL("toggled(bool)"), self.updateView)

        self.updateView()

    def updateView(self):
        minDate = datetimeFromQDate(self.ui.fromDateEdit.date())
        maxDate = datetimeFromQDate(self.ui.toDateEdit.date())
        if maxDate < minDate:
            minDate, maxDate = maxDate, minDate

        maxDate += timedelta(1)

        filters = [ \
            Task.q.status == "done", \
            Task.q.doneDate >= minDate, \
            Task.q.doneDate < maxDate \
            ]

        projectFilter = self.ui.projectLineEdit.text()
        if not projectFilter.isEmpty():
            filters.append(
                IN(
                    Task.q.project,
                    Select(Project.q.id, LIKE(Project.q.name, "%" + unicode(projectFilter) + "%"))
                ))

        tasks = Task.select(AND(*filters))


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
        if self.ui.showEmptyDaysCheckBox.isChecked():
            date = minDate.date()
            while date < maxDate.date():
                if not date in dct:
                    dct[date] = {}
                date += timedelta(1)

        html = TEMPLATE.render(dct=dct)
        self.ui.webView.setHtml(html)
