#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Command line oriented, sqlite powered, todo list

@author: Aurélien Gâteau <aurelien.gateau@free.fr>
@license: GPL v3 or later
"""
from optparse import OptionParser

def createOptionParser():
    """
    Return an option parser with common qyok options
    """
    parser = OptionParser()

    parser.add_option("-d", "--db", dest="filename",
                      help="TODO database", metavar="FILE")

    return parser
