# coding: utf-8
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class YDateEdit(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setFocusPolicy(Qt.StrongFocus)

        self._dateButton = QToolButton()
        self._dateButton.setPopupMode(QToolButton.InstantPopup)
        self._dateButton.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.setFocusProxy(self._dateButton)

        self._resetButton = QToolButton()
        self._resetButton.setText(u"⌫")
        self._resetButton.setToolButtonStyle(Qt.ToolButtonTextOnly)

        self._calendar = QCalendarWidget()
        action = QWidgetAction(self)
        action.setDefaultWidget(self._calendar)
        menu = QMenu()
        menu.addAction(action)
        self._dateButton.setMenu(menu)

        layout = QHBoxLayout(self)
        layout.setMargin(0)
        layout.addWidget(self._dateButton)
        layout.addWidget(self._resetButton)
        layout.addStretch()

        self._date = None

        QObject.connect(self._resetButton, SIGNAL("clicked()"), self.resetDate)
        QObject.connect(self._calendar, SIGNAL("clicked(QDate)"), self.setDate)
        QObject.connect(self._calendar, SIGNAL("activated(QDate)"), self.setDate)

        self._updateButtons()

    def _updateButtons(self):
        if self._date is None:
            self._dateButton.setText(self.tr("None"))
            self._resetButton.hide()
        else:
            self._dateButton.setText(self._date.toString())
            self._resetButton.show()

    def setDate(self, date):
        self._date = date
        self._dateButton.menu().close()
        self._updateButtons()

    def date(self):
        return self._date

    def resetDate(self):
        self.setDate(None)
