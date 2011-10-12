# -*- coding: UTF-8 -*-
import os
from datetime import datetime, timedelta

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *

from yokadi.db import Task

from jinja2 import Environment, FileSystemLoader

from ui_mainwindow import Ui_MainWindow
from addtaskdialog import AddTaskDialog
from qydateutils import datetimeFromQDate, qdateFromDatetime

import queries

QUERY_DUE = 0
QUERY_PROJECT = 1
QUERY_DONE = 2

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.centralWidget().layout().setMargin(0)
        self.setupQueryListWidget()
        self.setupProjectFilter()
        self.setupActions()

        self.dataDir = os.path.dirname(__file__)

        self.setupJinjaEnv()

        self.ui.fromDateEdit.setDate(QDate.currentDate().addDays(-7))
        self.ui.toDateEdit.setDate(QDate.currentDate())

        self.ui.webView.settings().setDefaultTextEncoding("utf-8")
        self.ui.webView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)

        for obj, signal in [
                (self.ui.fromDateEdit, "dateChanged(QDate)"),
                (self.ui.toDateEdit, "dateChanged(QDate)"),
                (self.projectLineEdit, "textChanged(QString)"),
                (self.ui.queryListWidget, "itemSelectionChanged()"),
            ]:
            QObject.connect(obj, SIGNAL(signal), self.updateQuery)

        QObject.connect(self.ui.queryListWidget, SIGNAL("itemSelectionChanged()"), self.updateFilterWidgets)

        QObject.connect(self.ui.webView, SIGNAL("linkClicked(const QUrl&)"), self.openUrl)

        self.updateFilterWidgets()
        self.updateQuery()

    def setupQueryListWidget(self):
        # Set widget width to be just a little wider than what is necessary to
        # show all items
        widget = self.ui.queryListWidget
        fm = QFontMetrics(widget.font())
        width = max(fm.width(widget.item(x).text()) for x in range(widget.count()))
        widget.setFixedWidth(width + 3 * fm.width("m"))


    def setupActions(self):
        self.ui.newTaskAction.setIcon(QIcon.fromTheme("document-new"))
        QObject.connect(self.ui.newTaskAction, SIGNAL("triggered()"), self.addTask)

        actions = [self.ui.newTaskAction]
        for action in actions:
            shortcut = action.shortcut()
            if not shortcut.isEmpty():
                toolTip = self.tr("%1 (%2)", "%1 is the tooltip text, %2 is the action shortcut") \
                    .arg(action.toolTip()) \
                    .arg(shortcut.toString())
                action.setToolTip(toolTip)

    def setupProjectFilter(self):
        self.projectLineEdit = QLineEdit()
        self.projectLineEdit.setPlaceholderText(self.tr("Project Filter"))

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.ui.toolBar.addWidget(spacer)

        self.ui.toolBar.addWidget(self.projectLineEdit)

    def setupJinjaEnv(self):
        self.jinjaEnv = Environment()
        self.jinjaEnv.filters["dueDateCssClass"] = queries.dueDateCssClass
        self.jinjaEnv.filters["formatDate"] = queries.formatDate
        self.jinjaEnv.filters["formatDueDate"] = queries.formatDueDate

        tmplDir = os.path.join(self.dataDir, "templates")
        self.jinjaEnv.loader = FileSystemLoader(tmplDir)

    def updateFilterWidgets(self):
        queryType = self.ui.queryListWidget.currentRow()
        self.ui.doneWidget.setVisible(queryType == QUERY_DONE)

    def updateView(self):
        args = self.query.run()
        tmpl = self.jinjaEnv.get_template(self.query.templateName)
        html = tmpl.render(args)
        baseUrl = QUrl.fromLocalFile(os.path.join(self.dataDir, "static/"))
        self.ui.webView.setHtml(html, baseUrl)
        self.ui.webView.page().mainFrame().addToJavaScriptWindowObject("qtWindow", self)

    def updateQuery(self):
        queryType = self.ui.queryListWidget.currentRow()
        queryClasses = {
            QUERY_DUE: queries.DueQuery,
            QUERY_PROJECT: queries.ProjectQuery,
            QUERY_DONE: queries.DoneQuery,
            }
        self.query = queryClasses[queryType]()

        # Project
        projectName = self.projectLineEdit.text()
        if not projectName.isEmpty():
            self.query.projectName = unicode(projectName)

        # Status
        if queryType == QUERY_DONE:
            minDate = datetimeFromQDate(self.ui.fromDateEdit.date())
            maxDate = datetimeFromQDate(self.ui.toDateEdit.date())
            if maxDate < minDate:
                minDate, maxDate = maxDate, minDate

            maxDate += timedelta(1)
            self.query.minDate = minDate
            self.query.maxDate = maxDate

        self.updateView()

    def updateViewAndKeepPosition(self):
        frame = self.ui.webView.page().currentFrame()
        pos = frame.scrollPosition()
        self.updateView()
        frame.setScrollPosition(pos)

    def openUrl(self, url):
        QDesktopServices.openUrl(url)

    def addTask(self):
        dlg = AddTaskDialog(task=None, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.updateViewAndKeepPosition()

    def editTask(self, taskId):
        task = Task.get(taskId)
        dlg = AddTaskDialog(task, self)
        if dlg.exec_() == QDialog.Accepted:
            self.updateViewAndKeepPosition()

    def removeTask(self, taskId):
        Task.delete(taskId)
        self.updateViewAndKeepPosition()

    @pyqtSlot(int, str)
    def setTaskStatus(self, taskId, status):
        task = Task.get(taskId)
        status = unicode(status)
        task.status = status
        if status == "done":
            task.doneDate = datetime.now()

    @pyqtSlot(int, str)
    def showTaskPopup(self, taskId, buttonId):
        frame = self.ui.webView.page().mainFrame()
        element = frame.findFirstElement(buttonId)
        assert element
        rect = element.geometry()
        topLeft = self.ui.webView.mapToGlobal(rect.topLeft() - frame.scrollPosition())

        menu = QMenu()
        edit = menu.addAction(self.tr("Edit"))
        rmMenu = menu.addMenu(self.tr("Remove"))
        remove = rmMenu.addAction(self.tr("Do It"))
        menuHeight = menu.sizeHint().height()
        screenHeight = QApplication.desktop().screenGeometry(self).height()

        if topLeft.y() + menuHeight < screenHeight:
            pos = QPoint(topLeft.x(), topLeft.y() + rect.height())
        else:
            pos = QPoint(topLeft.x(), topLeft.y() - menuHeight)

        action = menu.exec_(pos)

        if action == edit:
            self.editTask(taskId)
        elif action == remove:
            self.removeTask(taskId)
