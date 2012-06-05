# coding: utf-8
from PyQt4.QtCore import *
from PyQt4.QtGui import *

TAB_STOP = 4

class QYTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        QPlainTextEdit.__init__(self, parent)
        self.setFont(QFont("Mono"))

    def event(self, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                self.indent()
                event.accept()
                return True
            elif event.key() == Qt.Key_Backtab:
                self.dedent()
                event.accept()
                return True
        return QPlainTextEdit.event(self, event)

    def indent(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.insertText(TAB_STOP * " ")

    def dedent(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.StartOfLine)
        for x in range(TAB_STOP):
            cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
            if cursor.selectedText() == " ":
                cursor.removeSelectedText()
            else:
                return
