#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Command line oriented, sqlite powered, todo list

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""
import os
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from yokadi import db

import qymain
from logdialog import LogDialog

def main(argv):
    app = QApplication(argv)
    parser = qymain.createOptionParser()
    options, args = parser.parse_args(argv)
    db.connectDatabase(options.filename)

    dlg = LogDialog()
    dlg.show()
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
