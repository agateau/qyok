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
    font-size: 120%;
    margin: 0;
    padding: 0;
    padding-top: 1em;
}
h1:first-child {
    padding-top: 0;
}
ul {
    margin: 0;
}
</style>
</head>
<body>
{% for project in projects %}
    <h1>{{ project }}</h1>
    <ul>
    {% for task in taskDict[project] %}
        <li>{{ task }}</li>
    {% endfor %}
    </ul>
{% endfor %}
</body>
</html>
""")

class LogDialog(QDialog):
    def __init__(self):
        super(LogDialog, self).__init__()
        self.ui = Ui_LogDialog()
        self.ui.setupUi(self)

        QObject.connect(self.ui.dateEdit, SIGNAL("dateChanged(QDate)"), self.updateView)
        self.ui.dateEdit.setFocus()
        self.ui.dateEdit.setDate(QDate.currentDate())

        self.ui.webView.settings().setDefaultTextEncoding("utf-8")

    def updateView(self):
        qdate = self.ui.dateEdit.date()
        minDate = datetime(qdate.year(), qdate.month(), qdate.day())
        maxDate = minDate + timedelta(1)
        lst = Task.select(AND( \
            Task.q.status == "done", \
            Task.q.doneDate >= minDate, \
            Task.q.doneDate < maxDate, \
            ))

        taskDict = {}
        for task in lst:
            project = task.project.name
            if not project in taskDict:
                taskDict[project] = []
            taskDict[project].append(task.title)

        projects = taskDict.keys()
        projects.sort()
        html = TEMPLATE.render(projects=projects, taskDict=taskDict)
        self.ui.webView.setHtml(html)
