# -*- coding: UTF-8 -*-
from datetime import datetime

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from yokadi import db
from yokadi import dbutils
from yokadi import parseutils
from yokadi.yokadiexception import YokadiException

from ui_addtaskdialog import Ui_AddTaskDialog
from qydateutils import datetimeFromQDate, qdateFromDatetime

class AddTaskDialog(QDialog):
    def __init__(self, task=None, parent=None):
        super(AddTaskDialog, self).__init__(parent)
        self.task = task

        self.ui = Ui_AddTaskDialog()
        self.ui.setupUi(self)
        self.ui.errorLabel.hide()

        self.projectList = [x.name for x in db.Project.select(orderBy=db.Project.q.name)]
        completer = QCompleter(self.projectList, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.projectLineEdit.setCompleter(completer)

        self.ui.doneDateEdit.setDate(QDate.currentDate())

        font = QFont("Mono")
        self.ui.descriptionTextEdit.setFont(font)

        self.okButton = self.ui.buttonBox.button(QDialogButtonBox.Ok)

        if self.task is not None:
            self.initFromTask()
            self.okButton.setText(self.tr("&Update"))
        else:
            self.okButton.setText(self.tr("&Add Task"))

        QObject.connect(self.ui.projectLineEdit, SIGNAL("textChanged(QString)"), self.updateOkButton)
        QObject.connect(self.ui.titleLineEdit, SIGNAL("textChanged(QString)"), self.updateOkButton)
        self.updateOkButton()

    def initFromTask(self):
        self.ui.projectLineEdit.setText(self.task.project.name)
        title = parseutils.createLine("", self.task.title, self.task.getKeywordDict())
        self.ui.titleLineEdit.setText(title)
        if self.task.dueDate is not None:
            self.ui.dueDateEdit.setDate(qdateFromDatetime(self.task.dueDate))
        if self.task.description is not None:
            self.ui.descriptionTextEdit.setPlainText(self.task.description)
        if self.task.status == "done":
            self.ui.statusDone.setChecked(True)
            self.ui.doneDateEdit.setDate(qdateFromDatetime(self.task.doneDate))
        elif self.task.status == "started":
            self.ui.statusStarted.setChecked(True)
        elif self.task.status == "new":
            self.ui.statusNew.setChecked(True)
        else:
            raise Exception()

    def updateOkButton(self):
        self.okButton.setEnabled( \
            not self.ui.projectLineEdit.text().isEmpty() \
            and not self.ui.titleLineEdit.text().isEmpty() \
            )

    def showErrorMessage(self, msg):
        self.ui.errorLabel.setText(msg)
        self.ui.errorLabel.show()

    def setInitialDescription(self, text):
        self.ui.descriptionTextEdit.setPlainText(text)

    def confirmProjectCreation(self, projectName):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle(self.tr("Project does not exist"))
        box.setText(self.tr("Project \"%1\" does not exist. Create it?").arg(projectName))

        button = box.addButton(QMessageBox.Ok)
        button.setText(self.tr("&Create Project"))
        box.addButton(QMessageBox.Cancel)
        return box.exec_() == QMessageBox.Ok

    def confirmKeywordsCreation(self, keywords):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Question)
        title = self.tr("Some keywords do not exist")
        lst = "<ul>"
        lst += "".join("<li>{}</li>".format(k) for k in keywords)
        lst += "</ul>"
        text = self.tr("<qt>The following keywords do not exist.\n%1\nCreate them?</qt>").arg(lst)

        box.setWindowTitle(title)
        box.setText(text)
        button = box.addButton(QMessageBox.Ok)
        button.setText(self.tr("&Create Keywords"))
        box.addButton(QMessageBox.Cancel)
        return box.exec_() == QMessageBox.Ok

    def accept(self):
        projectName = unicode(self.ui.projectLineEdit.text())
        if not projectName in self.projectList:
            if not self.confirmProjectCreation(projectName):
                return

        line = projectName + u" " + unicode(self.ui.titleLineEdit.text())
        projectName, title, keywordDict = parseutils.parseLine(line)
        newKeywords = [k for k in keywordDict if len(list(db.Keyword.selectBy(name=k))) == 0]
        if len(newKeywords) > 0:
            if not self.confirmKeywordsCreation(newKeywords):
                return

        if self.task is None:
            try:
                task = dbutils.addTask(projectName, title, keywordDict, interactive=False)
            except YokadiException, exc:
                self.showErrorMessage(str(exc))
                return
            if not task:
                self.showErrorMessage("Task not created.")
                return
        else:
            try:
                project = dbutils.getOrCreateProject(projectName, interactive=False)
            except YokadiException, exc:
                self.showErrorMessage(str(exc))
                return
            task = self.task
            dbutils.createMissingKeywords(keywordDict.keys(), interactive=False)
            dbutils.updateTask(task, project.name, title, keywordDict)

        task.description = unicode(self.ui.descriptionTextEdit.toPlainText())
        task.dueDate = datetimeFromQDate(self.ui.dueDateEdit.date())

        if self.ui.statusStarted.isChecked():
            task.status = "started"
        elif self.ui.statusDone.isChecked():
            task.status = "done"
            task.doneDate = datetimeFromQDate(self.ui.doneDateEdit.date())

        super(AddTaskDialog, self).accept()

