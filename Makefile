all:
	pyuic4 addtaskdialog.ui -o ui_addtaskdialog.py

clean:
	-rm *.pyc ui_*.py
