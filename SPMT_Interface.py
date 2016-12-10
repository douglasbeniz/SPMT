#!/usr/bin/env python3.4
import sys
import time

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QCheckBox, QComboBox, QDateTimeEdit, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListView, QListWidget, QListWidgetItem, QPushButton, QSpinBox, QStackedWidget, QVBoxLayout, QWidget
from PyQt5.uic import loadUi

class DemoImpl(QMainWindow):
    def __init__(self, *args):
        super(DemoImpl, self).__init__(*args)
        self.mainLayout = loadUi('SPMT_UI.ui', self)
        self.pushButton_exit.clicked.connect(self.exit)
        self.pushButton_reset.clicked.connect(self.reset)
        self.pushButton_runProgramm.clicked.connect(self.runProgramm)
    
    #@pyqtSlot()
    def runProgramm(self):
        i = 0
        vet = [1,2,3,4]
        
        for i in range(10):
            item = QListWidgetItem("Item %i" % i)
            self.mainLayout.listWidget_logView.addItem(item)
        
        for s in "This is a demo \n;".split(";"):
            pass
            #self.listView_logView.insertItem(s)
        #self.listView_logView.addItem(vet)
            #i = i + 1
            #vet.append(s)
        #self.listView_logView.addItem("\n")
        #a = self.lineEdit.copy()
        #a = str(a)
        self.mainLayout.lineEdit_initialVoltage.setText("3.14")
    
    #@pyqtSlot()
    def reset(self):
        #self.label.setText("Reset")
        #QMessageBox.information(None,"Hello!","You Clicked: \n"+index.data().toString())
        self.mainLayout.lineEdit_initialVoltage.clear()        

    #@pyqtSlot()
    def exit(self):
        #self.label.clear()
        #self.list.clear()
        time.sleep(1)
        #self.textBrowser.clear()
        sys.exit()

app = QApplication(sys.argv)
widget = DemoImpl()
widget.show()
sys.exit(app.exec_())
