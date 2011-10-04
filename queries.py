# -*- coding: UTF-8 -*-
from datetime import datetime

from PyQt4.QtCore import QCoreApplication

from sqlobject import AND, OR, LIKE, IN
from sqlobject.sqlbuilder import Select

from yokadi.db import Task, Project

def formatDate(date):
    """
    strftime may return a string with accent ("August" in fr is "Août" for
    example), so we need to turn it into proper unicode.
    """
    return unicode(date.strftime("%A %d %B %Y"), "utf-8")

def __tr(txt):
    return QCoreApplication.translate("", txt)

def formatDueDate(dueDate):
    today = datetime.now()
    remaining = (dueDate.date() - today.date()).days
    if remaining < 0:
        txt = __tr("%1 days overdue").arg(-remaining)
    elif remaining == 0:
        txt = __tr("Due today")
    elif remaining == 1:
        txt = __tr("Due tomorrow")
    elif remaining < 7:
        txt = __tr("%1 days left").arg(remaining)
    else:
        txt = __tr("%1 weeks left").arg(remaining / 7)
    return unicode(txt)

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

class Item(object):
    __slots__ = ["task", "grp1", "grp2"]

class Query(object):
    __slots__ = ["projectName", "_filters"]
    def __init__(self):
        self.projectName = None
        self._filters = []

    def _addProjectFilter(self):
        if self.projectName is None:
            return
        self._filters.append(
            IN(
                Task.q.project,
                Select(Project.q.id, LIKE(Project.q.name, "%" + self.projectName + "%"))
            ))

    def run(self):
        self._filters = []
        self._addProjectFilter()

class DueQuery(Query):
    templateName = "index.html"
    __slots__ = ["dueDate"]

    def __init__(self):
        super(DueQuery, self).__init__()
        self.dueDate = None

    def run(self):
        super(DueQuery, self).run()
        self._filters.append(OR(Task.q.status == "new", Task.q.status == "started"))
        self._filters.append(Task.q.dueDate < self.dueDate)
        tasks = Task.select(AND(*self._filters))

        lst = []
        for task in tasks:
            item = Item()
            item.task = task
            item.grp1 = task.dueDate.date()
            item.grp2 = task.project.name
            lst.append(item)

        fmt1 = formatDate
        return dict(lst=lst, fmt1=fmt1)

class ProjectQuery(Query):
    templateName = "index.html"
    def run(self):
        super(ProjectQuery, self).run()
        self._filters.append(OR(Task.q.status == "new", Task.q.status == "started"))
        tasks = Task.select(AND(*self._filters))

        lst = []
        for task in tasks:
            item = Item()
            item.task = task
            item.grp1 = task.project.name
            item.grp2 = ""
            lst.append(item)

        fmt1 = lambda x: x
        return dict(lst=lst, fmt1=fmt1)

class DoneQuery(Query):
    templateName = "done.html"
    __slots__ = ["minDate", "maxDate"]

    def  __init__(self):
        super(DoneQuery, self).__init__()
        self.minDate = None
        self.maxDate = None

    def run(self):
        super(DoneQuery, self).run()
        self._filters.append(Task.q.status == "done")
        if self.minDate is not None:
            self._filters.append(Task.q.doneDate >= self.minDate)
        if self.maxDate is not None:
            self._filters.append(Task.q.doneDate < self.maxDate)
        tasks = Task.select(AND(*self._filters))

        lst = []
        for task in tasks:
            item = Item()
            item.task = task
            item.grp1 = task.doneDate.date()
            item.grp2 = task.project.name
            lst.append(item)

        fmt1 = formatDate
        return dict(lst=lst, fmt1=fmt1)

