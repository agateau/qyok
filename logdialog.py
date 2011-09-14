# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from sqlobject import AND

from yokadi.db import Task

from ui_logdialog import Ui_LogDialog

def u8(*args):
    def _u8(txt):
        return txt.encode("utf-8")
    if len(args) == 1:
        return _u8(args[0])
    else:
        return [_u8(x) for x in args]

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

        lines = []
        lines.append("<html><body>")
        projects = taskDict.keys()
        projects.sort()
        for project in projects:
            lines.append("<h1>{}</h1>".format(u8(project)))
            lines.append("<ul>")
            for task in taskDict[project]:
                lines.append("<li>{}</li>".format(u8(task)))
            lines.append("</ul>")
        lines.append("</body></html>")

        self.ui.webView.setHtml(QString.fromUtf8("\n".join(lines)))
