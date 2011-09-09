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

        project_list = db.Project.select(orderBy=db.Project.q.name)
        lst = [x.name for x in project_list]
        completer = QCompleter(lst, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.projectLineEdit.setCompleter(completer)

        self.ui.doneDateEdit.setDate(QDate.currentDate())

        self.ui.buttonBox.button(QDialogButtonBox.Ok).setText(self.tr("Add Task"))

    def showErrorMessage(self, msg):
        self.ui.errorLabel.setText(msg)
        self.ui.errorLabel.show()

    def accept(self):
        line = unicode(self.ui.projectLineEdit.text()) + u" " + unicode(self.ui.titleLineEdit.text())
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

