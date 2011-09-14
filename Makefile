all:
	pyuic4 addtaskdialog.ui -o ui_addtaskdialog.py
	pyuic4 logdialog.ui -o ui_logdialog.py

clean:
	-rm *.pyc ui_*.py
