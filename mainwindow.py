# -*- coding: UTF-8 -*-
import os
import logging
from datetime import datetime, timedelta

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *

from yokadi.db import Task
from yokadi import parseutils

from jinja2 import Environment, FileSystemLoader

import markdown

from ui_mainwindow import Ui_MainWindow
from addtaskdialog import AddTaskDialog
from csspalette import CssPalette
from qydateutils import datetimeFromQDate, qdateFromDatetime
from webpage import WebPage

import queries

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.dataDir = os.path.dirname(__file__)

        self.setupQueryList()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.centralWidget().layout().setMargin(0)
        self.setupQueryListWidget()
        self.setupFilter()
        self.setupActions()

        self.setupJinjaEnv()
        self.setupFilterWidgets()

        for obj, signal in [
                (self.ui.fromDateEdit, "dateChanged(QDate)"),
                (self.ui.toDateEdit, "dateChanged(QDate)"),
                (self.filterLineEdit, "textEdited(QString)"),
            ]:
            QObject.connect(obj, SIGNAL(signal), self.updateQuery)

        QObject.connect(self.ui.queryListWidget, SIGNAL("itemSelectionChanged()"), self.onCurrentQueryChanged)

        QObject.connect(self.ui.webView, SIGNAL("linkClicked(const QUrl&)"), self.openUrl)

        self.updateFilterWidgets()
        self.updateQuery()

    def setupQueryList(self):
        self.query = None
        self.queryList = []

        self.queryList.append(queries.DueQuery())
        self.queryList.append(queries.ProjectQuery("All Projects"))

        projectQueryFileName = os.path.expanduser("~/.config/qyok/projects.yaml")
        if os.path.exists(projectQueryFileName):
            self.queryList.extend(queries.loadProjectQueries(projectQueryFileName))

        self.queryList.append(queries.DoneQuery())

    def setupQueryListWidget(self):
        widget = self.ui.queryListWidget

        # Create items and associated shortcuts
        for index, query in enumerate(self.queryList):
            if index < 12:
                label = query.name + " (F%d)" % (index + 1)
                shortcut = QShortcut("F%d" % (index + 1), self)
                shortcut.setProperty("row", index)
                shortcut.activated.connect(self.onQueryShortcutActivated)
            else:
                label = query.name
            item = QListWidgetItem(label, widget)

        # Set widget width to be just a little wider than what is necessary to
        # show all items
        fm = QFontMetrics(widget.font())
        width = max(fm.width(widget.item(x).text()) for x in range(widget.count()))
        widget.setFixedWidth(width + 3 * fm.width("m"))

        # Set item heights to twice the font size so that they are easier to click
        sh = QSize(width, fm.height() * 2)
        for idx in range(widget.count()):
            widget.item(idx).setSizeHint(sh)

        widget.setCurrentRow(0)

    def setupFilterWidgets(self):
        self.ui.fromDateEdit.setDate(QDate.currentDate().addDays(-7))
        self.ui.toDateEdit.setDate(QDate.currentDate())
        pal = QPalette(self)
        bg = pal.window().color()
        gradient = QLinearGradient(0, 0, 0, self.ui.doneFrame.height())
        gradient.setColorAt(0, bg.darker(150))
        gradient.setColorAt(0.2, bg.darker(120))
        pal.setBrush(QPalette.Window, QBrush(gradient))
        pal.setBrush(QPalette.Button, bg)
        self.ui.doneFrame.setPalette(pal)

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

    def setupFilter(self):
        self.filterLineEdit = QLineEdit()
        self.filterLineEdit.setPlaceholderText(self.tr("Filter (Ctrl+F)"))

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.ui.toolBar.addWidget(spacer)

        self.ui.toolBar.addWidget(self.filterLineEdit)

        shortcut = QShortcut(self)
        shortcut.setKey(Qt.CTRL + Qt.Key_F)
        shortcut.activated.connect(self.filterLineEdit.setFocus)

    def setupJinjaEnv(self):
        self.jinjaEnv = Environment()
        self.jinjaEnv.filters["dueDateCssClass"] = queries.dueDateCssClass
        self.jinjaEnv.filters["formatDate"] = queries.formatDate
        self.jinjaEnv.filters["formatDueDate"] = queries.formatDueDate
        self.jinjaEnv.filters["markdown"] = markdown.markdown

        tmplDir = os.path.join(self.dataDir, "templates")
        self.jinjaEnv.loader = FileSystemLoader(tmplDir)

    def onQueryShortcutActivated(self):
        row, ok = self.sender().property("row").toInt()
        if ok:
            self.ui.queryListWidget.setCurrentRow(row)

    def onCurrentQueryChanged(self):
        row = self.ui.queryListWidget.currentRow()
        query = self.queryList[row]

        defaultFilters = []
        if query.defaultProjectName is not None:
            defaultFilters.append(query.defaultProjectName)
        defaultFilters.extend(["@" + x for x in query.defaultKeywordFilters])
        self.filterLineEdit.setText(" ".join(defaultFilters))
        self.updateQuery()

        self.updateFilterWidgets()

    def updateFilterWidgets(self):
        self.ui.doneFrame.setVisible(isinstance(self.query, queries.DoneQuery))

    def generateHtml(self):
        args = self.query.run()
        args["palette"] = CssPalette(self.palette())
        tmpl = self.jinjaEnv.get_template(self.query.templateName)
        return tmpl.render(args)

    def updateView(self):
        page = WebPage(logger=None, parent=self)
        page.setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        page.mainFrame().addToJavaScriptWindowObject("qtWindow", self)
        self.ui.webView.setPage(page)

        html = self.generateHtml()
        # baseUrl must end with a trailing '/' otherwise QWebView won't be able
        # to load files from there
        baseUrl = QUrl.fromLocalFile(os.path.join(self.dataDir, "static/"))
        self.ui.webView.setHtml(html, baseUrl)

    def updateQuery(self):
        row = self.ui.queryListWidget.currentRow()
        self.query = self.queryList[row]

        # Project
        projectName, keywordFilters = parseutils.extractKeywords(unicode(self.filterLineEdit.text()))
        self.query.projectName = projectName
        self.query.keywordFilters = keywordFilters

        # Status
        if isinstance(self.query, queries.DoneQuery):
            minDate = datetimeFromQDate(self.ui.fromDateEdit.date())
            maxDate = datetimeFromQDate(self.ui.toDateEdit.date())
            if minDate is not None and maxDate is not None and maxDate < minDate:
                minDate, maxDate = maxDate, minDate

            if maxDate is not None:
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
