# -*- coding: UTF-8 -*-
class CssColor(object):
    def __init__(self, qcolor):
        self.qcolor = qcolor

    def darker(self, percent):
        return CssColor(self.qcolor.darker(percent))

    def lighter(self, percent):
        return CssColor(self.qcolor.lighter(percent))

    def __str__(self):
        return unicode(self.qcolor.name())
