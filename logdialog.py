# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from sqlobject import AND

from yokadi.db import Task

from ui_logdialog import Ui_LogDialog

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

        titles = [x.title for x in lst]

        lines = []
        lines.append("<html><body>")
        lines.append("<ul>")
        for title in titles:
            lines.append("<li>{}</li>".format(title.encode("utf-8")))
        lines.append("</ul>")
        lines.append("</body></html>")

        self.ui.webView.setHtml(QString.fromUtf8("\n".join(lines)))
