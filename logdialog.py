# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from sqlobject import AND, OR, LIKE, IN
from sqlobject.sqlbuilder import Select

from jinja2 import Environment

from yokadi.db import Task, Project

from ui_logdialog import Ui_LogDialog

def formatDate(date):
    """
    strftime may return a string with accent ("August" in fr is "Août" for
    example), so we need to turn it into proper unicode.
    """
    return unicode(date.strftime("%A %d %B %Y"), "utf-8")

def formatDueDate(dueDate):
    today = datetime.now()
    remaining = (dueDate.date() - today.date()).days
    if remaining == 0:
        return unicode(QApplication.translate("", "today"))
    elif remaining == 1:
        return unicode(QApplication.translate("", "tomorrow"))
    else:
        return unicode(dueDate.strftime("%x"), "utf-8")

def dueDateCssClass(task):
    done = task.status == "done"
    if done:
        refDate = task.doneDate
    else:
        refDate = datetime.now()
    remaining = (task.dueDate.date() - refDate.date()).days

    if done:
        if remaining < 0:
            return "due-date-overdue"
        else:
            return ""

    if remaining < 0:
        return "due-date-overdue"
    elif remaining == 0:
        return "due-date-today"
    elif remaining < 7:
        return "due-date-week"
    else:
        return ""

ENVIRONMENT = Environment()
ENVIRONMENT.filters["dueDateCssClass"] = dueDateCssClass
ENVIRONMENT.filters["formatDate"] = formatDate
ENVIRONMENT.filters["formatDueDate"] = formatDueDate
TEMPLATE = ENVIRONMENT.from_string(u"""
<html>
<head>
<style>
body {
    font-family: sans-serif;
    font-size: 10pt;
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
    list-style-type: none;
}
li {
    margin: 0;
    padding: 0.2em;
    border-left: 1px solid #666;
    border-right: 1px solid #666;
    border-bottom: 1px dotted #666;
    background-color: white;
}
li:first-child {
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border-top: 1px solid #666;
}
li:last-child {
    border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
    border-bottom: 1px solid #666;
}
.group1 {
    margin: 6px;
    padding: 6px;
}

.due-date {
    float: right;
    border-radius: 3px;
    padding: 0 2px;
}

.due-date-overdue {
    background-color: red;
    color: white;
}

.due-date-today {
    background-color: orange;
}

.due-date-week {
    background-color: yellow;
}

</style>
</head>
<body>
{% for grp1, lst in lst|groupby('grp1') %}
    <div class='group1'>
    <h1>{{ fmt1(grp1) }}</h1>
    {% for grp2, lst in lst|groupby('grp2') %}
        <h2>{{ grp2|e }}</h2>
        <ul>
        {% for item in lst %}
            <li>
            {% if item.task.dueDate %}
                <span class='due-date {{ item.task|dueDateCssClass }}'>
                    Due: {{ item.task.dueDate|formatDueDate }}
                </span>
            {% endif %}
            {{ item.task.title|e }}
            </li>
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

QUERY_DUE = 0
QUERY_PROJECT = 1
QUERY_DONE = 2

class LogDialog(QDialog):
    def __init__(self):
        super(LogDialog, self).__init__()
        self.ui = Ui_LogDialog()
        self.ui.setupUi(self)
        self.layout().setMargin(0)

        self.ui.fromDateEdit.setDate(QDate.currentDate().addDays(-7))
        self.ui.toDateEdit.setDate(QDate.currentDate())
        self.ui.dueDateEdit.setDate(QDate.currentDate())

        self.ui.webView.settings().setDefaultTextEncoding("utf-8")

        for obj, signal in [
                (self.ui.fromDateEdit, "dateChanged(QDate)"),
                (self.ui.toDateEdit, "dateChanged(QDate)"),
                (self.ui.projectLineEdit, "textChanged(QString)"),
                (self.ui.queryListWidget, "itemSelectionChanged()"),
            ]:
            QObject.connect(obj, SIGNAL(signal), self.updateView)

        QObject.connect(self.ui.queryListWidget, SIGNAL("itemSelectionChanged()"), self.updateFilterWidgets)
        self.updateFilterWidgets()
        self.updateView()

    def updateFilterWidgets(self):
        queryType = self.ui.queryListWidget.currentRow()
        self.ui.dueWidget.setVisible(queryType == QUERY_DUE)
        self.ui.doneWidget.setVisible(queryType == QUERY_DONE)

    def updateView(self):
        filters = []
        queryType = self.ui.queryListWidget.currentRow()

        # Project
        wantedProject = self.ui.projectLineEdit.text()
        if not wantedProject.isEmpty():
            filters.append(
                IN(
                    Task.q.project,
                    Select(Project.q.id, LIKE(Project.q.name, "%" + unicode(wantedProject) + "%"))
                ))

        # Status
        statusFilters = []
        if queryType == QUERY_DONE:
            minDate = datetimeFromQDate(self.ui.fromDateEdit.date())
            maxDate = datetimeFromQDate(self.ui.toDateEdit.date())
            if maxDate < minDate:
                minDate, maxDate = maxDate, minDate

            maxDate += timedelta(1)
            doneFilter = AND( \
                Task.q.status == "done", \
                Task.q.doneDate >= minDate, \
                Task.q.doneDate < maxDate \
                )
            statusFilters.append(doneFilter)
        else:
            statusFilters.append(Task.q.status == "new")
            statusFilters.append(Task.q.status == "started")

        filters.append(OR(*statusFilters))

        # Due date
        if queryType == QUERY_DUE:
            dueDate = datetimeFromQDate(self.ui.dueDateEdit.date()) + timedelta(1)
            filters.append(Task.q.dueDate < dueDate)

        tasks = Task.select(AND(*filters))

        lst = []
        class Item(object):
            __slots__ = ["task", "grp1", "grp2"]
        for task in tasks:
            item = Item()
            item.task = task
            if queryType == QUERY_DUE:
                item.grp1 = task.dueDate.date()
                item.grp2 = task.project.name
            elif queryType == QUERY_PROJECT:
                item.grp1 = task.project.name
                item.grp2 = ""
            elif queryType == QUERY_DONE:
                item.grp1 = task.doneDate.date()
                item.grp2 = task.project.name
            else:
                raise Exception()
            lst.append(item)

        if queryType == QUERY_DUE:
            fmt1 = formatDate
        elif queryType == QUERY_PROJECT:
            fmt1 = lambda x: x
        elif queryType == QUERY_DONE:
            fmt1 = formatDate
        else:
            raise Exception()

        html = TEMPLATE.render(lst=lst, fmt1=fmt1)
        self.ui.webView.setHtml(html)
