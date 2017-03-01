#!/usr/bin/env python3.4
import sys
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from datetime import datetime
from threading import Thread
from SPMT_Project import *

class SPMT_Interface(QMainWindow):
    def __init__(self, *args):
        super(SPMT_Interface, self).__init__(*args)
        # 
        self.mainLayout = loadUi('SPMT_UI.ui', self)

        # Set initial configuration
        self.initialSetup()

        # Perform connections with methods of execution
        self.comboBox_numberOfChannels.currentIndexChanged.connect(self.changedNumberChannels)
        self.pushButton_exit.clicked.connect(self.exit)
        self.pushButton_reset.clicked.connect(self.reset)
        self.pushButton_runProgramm.clicked.connect(self.runProgramm)

        # Main object of SPMT project (execution program)
        self.orchestrator = Orchestrator()
    
        # Connect all slots
        self.orchestrator.informExecution.connect(self.informExecution)
        self.orchestrator.fillTable.connect(self.fillTable)
        self.orchestrator.resetButtons.connect(self.resetButtons)

    #@pyqtSlot()
    def runProgramm(self):
        # Set parameter values according to those in UI
        # -------------------------
        # Initial setup tab
        self.orchestrator.initialVoltage         = float(self.mainLayout.lineEdit_initialVoltage.text())
        self.orchestrator.maxVoltageError        = float(self.mainLayout.lineEdit_maxVoltageError.text())
        self.orchestrator.voltageFactor          = float(eval(self.mainLayout.lineEdit_voltageFactor.text()))
        self.orchestrator.currentFactor          = float(eval(self.mainLayout.lineEdit_currentFactor.text()))
        self.orchestrator.maxVMonError           = float(self.mainLayout.lineEdit_maxVMonError.text())
        self.orchestrator.maxIMonError           = float(self.mainLayout.lineEdit_maxIMonError.text())
        self.orchestrator.numberOfChannels       = int(self.comboBox_numberOfChannels.currentText())
        self.orchestrator.channelNumber          = int(self.lineEdit_channelNumber.text())
        # -------------------------
        # Dark count tab
        self.orchestrator.darkCountFreq          = int(self.mainLayout.lineEdit_darkCountFreq.text())
        self.orchestrator.darkCountPulses        = int(self.mainLayout.lineEdit_darkCountPulses.text())
        # -------------------------
        # Single photoelectron tab
        self.orchestrator.channelOfLED_1         = int(self.mainLayout.lineEdit_channelOfLED_1.text())
        self.orchestrator.singlePhVoltageLED_1   = float(self.mainLayout.lineEdit_singlePhVoltageLED_1.text())
        self.orchestrator.singlePhOptFreq        = int(self.mainLayout.lineEdit_singlePhOptFreq.text())
        self.orchestrator.singlePhOptPulses      = int(self.mainLayout.lineEdit_singlePhOptPulses.text())
        self.orchestrator.singlePhAcqFreq        = int(self.mainLayout.lineEdit_singlePhAcqFreq.text())
        self.orchestrator.singlePhAcqPulses      = int(self.mainLayout.lineEdit_singlePhAcqPulses.text())
        # -------------------------
        # Intense LED tab
        self.orchestrator.highIntensVoltageLED_1 = float(self.mainLayout.lineEdit_highIntensVoltageLED_1.text())
        self.orchestrator.highIntensOptFreq      = int(self.mainLayout.lineEdit_highIntensOptFreq.text())
        self.orchestrator.highIntensOptPulses    = int(self.mainLayout.lineEdit_highIntensOptPulses.text())
        self.orchestrator.highIntensAcqFreq      = int(self.mainLayout.lineEdit_highIntensAcqFreq.text())
        self.orchestrator.highIntensAcqPulses    = int(self.mainLayout.lineEdit_highIntensAcqPulses.text())
        # -------------------------
        # Low LED tab
        self.orchestrator.channelOfLED_2         = int(self.mainLayout.lineEdit_channelOfLED_2.text())
        self.orchestrator.channelOfLED_3         = int(self.mainLayout.lineEdit_channelOfLED_3.text())
        self.orchestrator.lowIntensVoltageLEDs   = float(self.mainLayout.lineEdit_lowIntensVoltageLEDs.text())
        self.orchestrator.lowIntensVoltageFactor = float(eval(self.mainLayout.lineEdit_lowIntensVoltageFactor.text()))
        self.orchestrator.lowIntensAcqFreq       = int(self.mainLayout.lineEdit_lowIntensAcqFreq.text())
        self.orchestrator.lowIntensAcqPulses     = int(self.mainLayout.lineEdit_lowIntensAcqPulses.text())
        # -------------------------
        # Linearity tab
        self.orchestrator.linearityVoltageFactor = float(eval(self.mainLayout.lineEdit_linearityVoltageFactor.text()))
        self.orchestrator.numberOfColpi          = int(self.mainLayout.lineEdit_numberOfColpi.text())
        self.orchestrator.numberOfSteps          = int(self.mainLayout.lineEdit_numberOfSteps.text())
        self.orchestrator.incrementLED_2         = float(self.mainLayout.lineEdit_incrementLED_2.text())
        self.orchestrator.incrementLED_3         = float(self.mainLayout.lineEdit_incrementLED_3.text())
        self.orchestrator.initialVoltageLED_2    = float(self.mainLayout.lineEdit_initialVoltageLED_2.text())
        self.orchestrator.initialVoltageLED_3    = float(self.mainLayout.lineEdit_initialVoltageLED_3.text())
        self.orchestrator.linearityAcqFreq       = int(self.mainLayout.lineEdit_linearityAcqFreq.text())
        
        # Set debug
        self.orchestrator.setDebug(debug=self.mainLayout.checkBox_debug.isChecked())

        # Call execution method from orchestrator...
        executeProgram = Thread(target=self.orchestrator.executeProgram)
        executeProgram.setDaemon(True)
        executeProgram.start()

        # Disable run button
        self.pushButton_runProgramm.setEnabled(False)
        self.pushButton_reset.setEnabled(True)
    
    def changedNumberChannels(self, index):
        if (index == 0):
            self.lineEdit_channelNumber.setEnabled(True)
            self.lineEdit_channelNumber.setText("0")
        else:
            self.lineEdit_channelNumber.setEnabled(False)

    #@pyqtSlot()
    def reset(self):
        self.initialSetup()
        self.orchestrator.reset()

        # Disable run button
        self.pushButton_runProgramm.setEnabled(True)
        self.pushButton_reset.setEnabled(False)

    #@pyqtSlot()
    def exit(self):
        self.orchestrator.reset()
        # wait a while
        sleep(3)
        self.close()

    def initialSetup(self):
        # Clean the history of execution
        self.mainLayout.listWidget_logView.clear()

        # Clean table values...
        for row in range(self.mainLayout.tableWidget_table.rowCount()):
            for col in range(self.mainLayout.tableWidget_table.columnCount()):
                self.mainLayout.tableWidget_table.setItem(row, col, QTableWidgetItem(""))

        # Set default parameters values for configuration
        # -------------------------
        # Initial setup tab
        self.mainLayout.lineEdit_initialVoltage.setText("1.75")
        self.mainLayout.lineEdit_maxVoltageError.setText("0.02")
        self.mainLayout.lineEdit_voltageFactor.setText("2.0")
        self.mainLayout.lineEdit_maxVMonError.setText("0.03")
        self.mainLayout.lineEdit_currentFactor.setText("((2100/2.5)*(100/66975))")
        self.mainLayout.lineEdit_maxIMonError.setText("0.03")
        # -------------------------
        # Dark count tab
        self.mainLayout.lineEdit_darkCountFreq.setText("100")
        self.mainLayout.lineEdit_darkCountPulses.setText("100000")
        # -------------------------
        # Single photoelectron tab
        self.mainLayout.lineEdit_channelOfLED_1.setText("8")
        self.mainLayout.lineEdit_singlePhVoltageLED_1.setText("2.5")
        self.mainLayout.lineEdit_singlePhOptFreq.setText("100")
        self.mainLayout.lineEdit_singlePhOptPulses.setText("5000")
        self.mainLayout.lineEdit_singlePhAcqFreq.setText("100")
        self.mainLayout.lineEdit_singlePhAcqPulses.setText("100000")
        # -------------------------
        # Intense LED tab
        self.mainLayout.lineEdit_highIntensVoltageLED_1.setText("7.0")
        self.mainLayout.lineEdit_highIntensOptFreq.setText("10")
        self.mainLayout.lineEdit_highIntensOptPulses.setText("150")
        self.mainLayout.lineEdit_highIntensAcqFreq.setText("10")
        self.mainLayout.lineEdit_highIntensAcqPulses.setText("600")
        # -------------------------
        # Low LED tab
        self.mainLayout.lineEdit_channelOfLED_2.setText("9")
        self.mainLayout.lineEdit_channelOfLED_3.setText("10")
        self.mainLayout.lineEdit_lowIntensVoltageLEDs.setText("1.25")
        self.mainLayout.lineEdit_lowIntensVoltageFactor.setText("(2100.0/2.5)")
        self.mainLayout.lineEdit_lowIntensAcqFreq.setText("10")
        self.mainLayout.lineEdit_lowIntensAcqPulses.setText("600")
        # -------------------------
        # Linearity tab
        self.mainLayout.lineEdit_linearityVoltageFactor.setText("(2.5/2100.0)")
        self.mainLayout.lineEdit_numberOfColpi.setText("30")
        self.mainLayout.lineEdit_numberOfSteps.setText("50")
        self.mainLayout.lineEdit_incrementLED_2.setText("0.15")
        self.mainLayout.lineEdit_incrementLED_3.setText("0.1")
        self.mainLayout.lineEdit_initialVoltageLED_2.setText("4.0")
        self.mainLayout.lineEdit_initialVoltageLED_3.setText("4.0")
        self.mainLayout.lineEdit_linearityAcqFreq.setText("10")

    def informExecution(self, message=""):
        self.mainLayout.listWidget_logView.addItem(datetime.now().strftime('%d/%m/%Y %H:%m:%S') + " - " + message)

    #@pyqtSlot()
    def fillTable(self, row, col, value):
        self.mainLayout.tableWidget_table.setItem(row, col, QTableWidgetItem(str(value)))

    #@pyqtSlot()
    def resetButtons(self):
        self.pushButton_reset.setEnabled(False)
        self.pushButton_runProgramm.setEnabled(True)

"""
Main()
"""
def main():
    app = QApplication(sys.argv)

    window = SPMT_Interface()
    window.setWindowTitle("SPMT Project")
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__": main()
