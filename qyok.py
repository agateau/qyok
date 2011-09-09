#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Command line oriented, sqlite powered, todo list

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""
import os
import sys
from optparse import OptionParser

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from yokadi import db

from addtaskdialog import AddTaskDialog

def main(argv):
    app = QApplication(argv)
    parser = OptionParser()

    parser.add_option("-d", "--db", dest="filename",
                      help="TODO database", metavar="FILE")

    options, args = parser.parse_args(argv)

    db.connectDatabase(options.filename)

    dlg = AddTaskDialog()
    return dlg.exec_()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
