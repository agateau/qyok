# coding: utf-8
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from yokadi import ydateutils
from yokadi.yokadiexception import YokadiException

from qydateutils import qdateFromDatetime

class QYDateEdit(QWidget):
    dateChanged = pyqtSignal(QDate)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed, QSizePolicy.SpinBox))
        self.setFocusPolicy(Qt.StrongFocus)

        self._lineEdit = QLineEdit()
        self._lineEdit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._lineEdit.setPlaceholderText(self.tr("None"))
        self._lineEdit.installEventFilter(self)
        self.setFocusProxy(self._lineEdit)

        self._resetButton = QToolButton()
        self._resetButton.setText(u"⨯")
        self._resetButton.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self._resetButton.setFocusPolicy(Qt.ClickFocus)

        # Prevent reset button from increasing widget height
        self._resetButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Ignored)

        layout = QHBoxLayout(self)
        layout.setMargin(0)
        layout.setSpacing(0)
        layout.addWidget(self._lineEdit)
        layout.addWidget(self._resetButton)
        layout.addStretch()

        self._date = QDate()

        QObject.connect(self._lineEdit, SIGNAL("textEdited(QString)"), self.slotTextEdited)
        QObject.connect(self._resetButton, SIGNAL("clicked()"), self.resetDate)

        self._updateLineEdit()
        self._updateResetButton()

    def _updateResetButton(self):
        self._resetButton.setEnabled(not self._lineEdit.text().isEmpty())

    def _updateLineEdit(self):
        if self._date.isNull():
            self._lineEdit.setText(QString())
        else:
            self._lineEdit.setText(self._date.toString(Qt.SystemLocaleShortDate))
        self._updateResetButton()

    def setDate(self, date):
        self._date = date
        self._updateLineEdit()

    def date(self):
        return self._date

    def resetDate(self):
        self.setDate(QDate())
        self.emitDateChanged()

    def slotTextEdited(self, text):
        if text.isEmpty():
            self.resetDate()
        else:
            pos = self.mapToGlobal(QPoint(0, 0))
            try:
                date = ydateutils.parseHumaneDateTime(unicode(text))
                self._date = qdateFromDatetime(date)
                tip = self._date.toString(Qt.SystemLocaleLongDate)
            except YokadiException, exc:
                tip = QString()
            QToolTip.showText(pos, tip, self, self.rect())
            self._updateResetButton()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusOut:
            self._updateLineEdit()
            self.emitDateChanged()
        return super(QYDateEdit, self).eventFilter(obj, event)

    def sizeHint(self):
        self.ensurePolished()
        self._lineEdit.ensurePolished()
        width = self._lineEdit.fontMetrics().width(" 88-88-8888 ") + self._resetButton.sizeHint().width()
        height = self._lineEdit.sizeHint().height()
        return QSize(width, height)

    def minimumSizeHint(self):
        return self.sizeHint()

    def emitDateChanged(self):
        self.dateChanged.emit(self._date)
