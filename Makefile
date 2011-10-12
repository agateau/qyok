all:
	pyuic4 addtaskdialog.ui -o ui_addtaskdialog.py
	pyuic4 mainwindow.ui -o ui_mainwindow.py

clean:
	-rm *.pyc ui_*.py
