from PyQt4.QtCore import *

from datetime import datetime

def datetimeFromQDate(qdate):
    if qdate is None or qdate.isNull():
        return None
    return datetime(qdate.year(), qdate.month(), qdate.day())

def qdateFromDatetime(dt):
    if dt is None:
        return QDate()
    return QDate(dt.year, dt.month, dt.day)
