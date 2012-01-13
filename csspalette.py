# -*- coding: UTF-8 -*-
from PyQt4.QtGui import *

class CssPalette(object):
    def __init__(self, qpalette):
        self.qpalette = qpalette

    def __getattr__(self, name):
        roleName = name[0].upper() + name[1:]
        role = eval("QPalette." + roleName)
        return CssColor(self.qpalette.color(role))

class CssColor(object):
    def __init__(self, qcolor):
        self.qcolor = qcolor

    def darker(self, percent):
        return CssColor(self.qcolor.darker(percent))

    def lighter(self, percent):
        return CssColor(self.qcolor.lighter(percent))

    def __str__(self):
        return unicode(self.qcolor.name())
