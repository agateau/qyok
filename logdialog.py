# -*- coding: UTF-8 -*-
import os
from datetime import datetime, timedelta

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *

from sqlobject import AND, OR, LIKE, IN
from sqlobject.sqlbuilder import Select

from jinja2 import Environment, FileSystemLoader

from yokadi.db import Task, Project

from ui_logdialog import Ui_LogDialog
from addtaskdialog import AddTaskDialog
from qydateutils import datetimeFromQDate, qdateFromDatetime

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

QUERY_DUE = 0
QUERY_PROJECT = 1
QUERY_DONE = 2

class LogDialog(QDialog):
    def __init__(self):
        super(LogDialog, self).__init__()
        self.ui = Ui_LogDialog()
        self.ui.setupUi(self)
        self.layout().setMargin(0)

        self.setupJinjaEnv()

        self.ui.fromDateEdit.setDate(QDate.currentDate().addDays(-7))
        self.ui.toDateEdit.setDate(QDate.currentDate())
        self.ui.dueDateEdit.setDate(QDate.currentDate())

        self.ui.webView.settings().setDefaultTextEncoding("utf-8")
        self.ui.webView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)

        for obj, signal in [
                (self.ui.fromDateEdit, "dateChanged(QDate)"),
                (self.ui.toDateEdit, "dateChanged(QDate)"),
                (self.ui.projectLineEdit, "textChanged(QString)"),
                (self.ui.queryListWidget, "itemSelectionChanged()"),
            ]:
            QObject.connect(obj, SIGNAL(signal), self.updateView)

        QObject.connect(self.ui.queryListWidget, SIGNAL("itemSelectionChanged()"), self.updateFilterWidgets)

        QObject.connect(self.ui.webView, SIGNAL("linkClicked(const QUrl&)"), self.dispatch)

        self.updateFilterWidgets()
        self.updateView()

    def setupJinjaEnv(self):
        self.jinjaEnv = Environment()
        self.jinjaEnv.filters["dueDateCssClass"] = dueDateCssClass
        self.jinjaEnv.filters["formatDate"] = formatDate
        self.jinjaEnv.filters["formatDueDate"] = formatDueDate

        tmplDir = os.path.join(os.path.dirname(__file__), "templates")
        self.jinjaEnv.loader = FileSystemLoader(tmplDir)

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

        tmpl = self.jinjaEnv.get_template("index.html")
        html = tmpl.render(lst=lst, fmt1=fmt1)
        self.ui.webView.setHtml(html)

    def updateViewAndKeepPosition(self):
        frame = self.ui.webView.page().currentFrame()
        pos = frame.scrollPosition()
        self.updateView()
        frame.setScrollPosition(pos)

    def dispatch(self, url):
        if not url.scheme().isEmpty():
            QDesktopServices.openUrl(url)
            return
        path = unicode(url.path())
        tokens = path.split("/")
        methodName = "do_" + tokens[0]
        if hasattr(self, methodName):
            getattr(self, methodName)(*tokens[1:])
        else:
            print "Unknown method", methodName

    def do_edit(self, idString):
        task = Task.get(int(idString))
        dlg = AddTaskDialog(task, self)
        if dlg.exec_() == QDialog.Accepted:
            self.updateViewAndKeepPosition()

    def do_setStatus(self, idString, status):
        task = Task.get(int(idString))
        task.status = status
        self.updateViewAndKeepPosition()
