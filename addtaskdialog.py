# -*- coding: UTF-8 -*-
from datetime import datetime

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from yokadi import db
from yokadi import dbutils
from yokadi import parseutils
from yokadi.yokadiexception import YokadiException

from ui_addtaskdialog import Ui_AddTaskDialog

class AddTaskDialog(QDialog):
    def __init__(self):
        super(AddTaskDialog, self).__init__()
        self.ui = Ui_AddTaskDialog()
        self.ui.setupUi(self)
        self.ui.errorLabel.hide()

        self.projectList = [x.name for x in db.Project.select(orderBy=db.Project.q.name)]
        completer = QCompleter(self.projectList, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.projectLineEdit.setCompleter(completer)

        self.ui.doneDateEdit.setDate(QDate.currentDate())

        self.okButton = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        self.okButton.setText(self.tr("&Add Task"))

        QObject.connect(self.ui.projectLineEdit, SIGNAL("textChanged(QString)"), self.updateOkButton)
        QObject.connect(self.ui.titleLineEdit, SIGNAL("textChanged(QString)"), self.updateOkButton)
        self.updateOkButton()

    def updateOkButton(self):
        self.okButton.setEnabled( \
            not self.ui.projectLineEdit.text().isEmpty() \
            and not self.ui.titleLineEdit.text().isEmpty() \
            )

    def showErrorMessage(self, msg):
        self.ui.errorLabel.setText(msg)
        self.ui.errorLabel.show()

    def confirmProjectCreation(self, projectName):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle(self.tr("Project does not exist"))
        box.setText(self.tr("Project \"%1\" does not exist. Create it?").arg(projectName))

        button = box.addButton(QMessageBox.Ok)
        button.setText(self.tr("&Create Project"))
        box.addButton(QMessageBox.Cancel)
        return box.exec_() == QMessageBox.Ok

    def accept(self):
        projectName = unicode(self.ui.projectLineEdit.text())
        if not projectName in self.projectList:
            if not self.confirmProjectCreation(projectName):
                return

        line = projectName + u" " + unicode(self.ui.titleLineEdit.text())
        projectName, title, keywordDict = parseutils.parseLine(line)

        try:
            task = dbutils.addTask(projectName, title, keywordDict, interactive=False)
        except YokadiException, exc:
            self.showErrorMessage(str(exc))
            return
        if not task:
            self.showErrorMessage("Task not created.")
            return

        if self.ui.statusStarted.isChecked():
            task.status = "started"
        elif self.ui.statusDone.isChecked():
            task.status = "done"
            qdate = self.ui.doneDateEdit.date()
            task.doneDate = datetime(qdate.year(), qdate.month(), qdate.day())

        super(AddTaskDialog, self).accept()

