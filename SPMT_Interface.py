#!/usr/bin/env python3.4
import sys
import time
import numpy
import csv

from PyQt5.QtGui import *
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
        self.pushButton_save.clicked.connect(self.save)
        self.pushButton_open.clicked.connect(self.restore)

        # Main object of SPMT project (execution program)
        self.orchestrator = Orchestrator()

        # Attributes
        self.configArray = []
    
        # Connect all slots
        self.orchestrator.informExecution.connect(self.informExecution)
        self.orchestrator.fillTable.connect(self.fillTable)
        self.orchestrator.resetButtons.connect(self.resetButtons)

    #@pyqtSlot()
    def runProgramm(self):
        # Store parameters
        self.__storeConfigParameters()

        # Call execution method from orchestrator...
        executeProgram = Thread(target=self.orchestrator.executeProgram)
        executeProgram.setDaemon(True)
        executeProgram.start()

        # Disable run button
        self.pushButton_runProgramm.setEnabled(False)
        self.pushButton_reset.setEnabled(True)
    

    def __storeConfigParameters(self):
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

        # -------------------------
        # HV identities
        highVoltageIDs = []

        for row in range (self.orchestrator.numberOfChannels):
            oneHVinfo = []

            oneHVinfo.append(str(self.mainLayout.tableWidget_inputID.item(row, 0).text()))
            oneHVinfo.append(str(self.mainLayout.tableWidget_inputID.item(row, 1).text()))
            oneHVinfo.append(float(self.mainLayout.tableWidget_inputID.item(row, 2).text()))
            oneHVinfo.append(float(self.mainLayout.tableWidget_inputID.item(row, 3).text()))

            # Append a new vector
            highVoltageIDs.append(oneHVinfo)

        self.orchestrator.highVoltageIDs = highVoltageIDs

        # Set debug
        self.orchestrator.setDebug(debug=self.mainLayout.checkBox_debug.isChecked())

        # -----------------------------------------------------------------
        # Now, store them on an array (attribute)...
        # -----------------------------------------------------------------
        self.configArray = []

        # -------------------------
        # Initial setup tab
        auxiliary = []
        auxiliary.append(float(self.mainLayout.lineEdit_initialVoltage.text()))
        auxiliary.append(float(self.mainLayout.lineEdit_maxVoltageError.text()))
        auxiliary.append(str(self.mainLayout.lineEdit_voltageFactor.text()))
        auxiliary.append(str(self.mainLayout.lineEdit_currentFactor.text()))
        auxiliary.append(float(self.mainLayout.lineEdit_maxVMonError.text()))
        auxiliary.append(float(self.mainLayout.lineEdit_maxIMonError.text()))
        auxiliary.append(int(self.comboBox_numberOfChannels.currentIndex()))
        auxiliary.append(int(self.lineEdit_channelNumber.text()))

        self.configArray.append(auxiliary)

        # -------------------------
        # Dark count tab
        auxiliary = []
        auxiliary.append(int(self.mainLayout.lineEdit_darkCountFreq.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_darkCountPulses.text()))

        self.configArray.append(auxiliary)

        # -------------------------
        # Single photoelectron tab
        auxiliary = []
        auxiliary.append(int(self.mainLayout.lineEdit_channelOfLED_1.text()))
        auxiliary.append(float(self.mainLayout.lineEdit_singlePhVoltageLED_1.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_singlePhOptFreq.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_singlePhOptPulses.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_singlePhAcqFreq.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_singlePhAcqPulses.text()))

        self.configArray.append(auxiliary)

        # -------------------------
        # Intense LED tab
        auxiliary = []
        auxiliary.append(float(self.mainLayout.lineEdit_highIntensVoltageLED_1.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_highIntensOptFreq.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_highIntensOptPulses.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_highIntensAcqFreq.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_highIntensAcqPulses.text()))

        self.configArray.append(auxiliary)

        # -------------------------
        # Low LED tab
        auxiliary = []
        auxiliary.append(int(self.mainLayout.lineEdit_channelOfLED_2.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_channelOfLED_3.text()))
        auxiliary.append(float(self.mainLayout.lineEdit_lowIntensVoltageLEDs.text()))
        auxiliary.append(str(self.mainLayout.lineEdit_lowIntensVoltageFactor.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_lowIntensAcqFreq.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_lowIntensAcqPulses.text()))

        self.configArray.append(auxiliary)

        # -------------------------
        # Linearity tab
        auxiliary = []
        auxiliary.append(str(self.mainLayout.lineEdit_linearityVoltageFactor.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_numberOfColpi.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_numberOfSteps.text()))
        auxiliary.append(float(self.mainLayout.lineEdit_incrementLED_2.text()))
        auxiliary.append(float(self.mainLayout.lineEdit_incrementLED_3.text()))
        auxiliary.append(float(self.mainLayout.lineEdit_initialVoltageLED_2.text()))
        auxiliary.append(float(self.mainLayout.lineEdit_initialVoltageLED_3.text()))
        auxiliary.append(int(self.mainLayout.lineEdit_linearityAcqFreq.text()))

        self.configArray.append(auxiliary)

        # -------------------------
        # HV identities
        highVoltageIDs = []

        for row in range (self.orchestrator.numberOfChannels):
            oneHVinfo = []

            oneHVinfo.append(str(self.mainLayout.tableWidget_inputID.item(row, 0).text()))
            oneHVinfo.append(str(self.mainLayout.tableWidget_inputID.item(row, 1).text()))
            oneHVinfo.append(float(self.mainLayout.tableWidget_inputID.item(row, 2).text()))
            oneHVinfo.append(float(self.mainLayout.tableWidget_inputID.item(row, 3).text()))

            # Append a new vector
            highVoltageIDs.append(oneHVinfo)
            # Store on attribures...
            self.configArray.append(oneHVinfo)

        self.orchestrator.highVoltageIDs = highVoltageIDs


    def changedNumberChannels(self, index):
        # Only the first channel info to fill-up...
        for row in range(self.mainLayout.tableWidget_inputID.rowCount()):
            for col in range(self.mainLayout.tableWidget_inputID.columnCount()):
                edit = ((index == 1) or ((index == 0) and (row == 0)))
                self.fillInputIDTable(row, col, "", edit=edit)

        # For a reference, fill-in some values
        self.fillInputIDTable(0, 0, "A7501PB")
        self.fillInputIDTable(0, 1, "066")
        self.fillInputIDTable(0, 2, "847.3831157965")
        self.fillInputIDTable(0, 3, "3.712840922")

        if (index == 0):
            self.lineEdit_channelNumber.setEnabled(True)
            self.lineEdit_channelNumber.setText("0")
        else:
            self.lineEdit_channelNumber.setEnabled(False)

    #@pyqtSlot()
    def reset(self):
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


    #@pyqtSlot()
    def save(self):
        #
        try:
            # --------------------------------------
            # Save configuration
            fileName = QFileDialog.getSaveFileName(self, 'Save config parameters', directory='./', filter='*.csv')

            if (fileName[0]):
                # 
                self.__storeConfigParameters()
                #
                #print(self.configArray)
                # 
                with open(fileName[0], "w") as out:
                    writer = csv.writer(out, quoting=csv.QUOTE_NONNUMERIC)
                    writer.writerows(self.configArray)
        except:
            pass


    #@pyqtSlot()
    def restore(self):
        #
        try:
            # --------------------------------------
            # Restore configuration
            data = []

            fileName = QFileDialog.getOpenFileName(self, 'Open config parameters', directory='./', filter='*.csv')

            fileCSV = open(fileName[0], 'r')

            openCSV = csv.reader(fileCSV)

            for row in openCSV:
                data.append(row)

            self.configArray = data
            #print(self.configArray)

            # -----------------------------------------------------------------
            # Set UI fields....
            # -----------------------------------------------------------------
            # Initial setup tab
            self.mainLayout.lineEdit_initialVoltage.setText(self.configArray[0][0])
            self.mainLayout.lineEdit_maxVoltageError.setText(self.configArray[0][1])
            self.mainLayout.lineEdit_voltageFactor.setText(self.configArray[0][2])
            self.mainLayout.lineEdit_currentFactor.setText(self.configArray[0][3])
            self.mainLayout.lineEdit_maxVMonError.setText(self.configArray[0][4])
            self.mainLayout.lineEdit_maxIMonError.setText(self.configArray[0][5])
            self.comboBox_numberOfChannels.setCurrentIndex(int(self.configArray[0][6]))
            self.lineEdit_channelNumber.setText(self.configArray[0][7])

            # -------------------------
            # Dark count tab
            self.mainLayout.lineEdit_darkCountFreq.setText(self.configArray[1][0])
            self.mainLayout.lineEdit_darkCountPulses.setText(self.configArray[1][1])

            # -------------------------
            # Single photoelectron tab
            self.mainLayout.lineEdit_channelOfLED_1.setText(self.configArray[2][0])
            self.mainLayout.lineEdit_singlePhVoltageLED_1.setText(self.configArray[2][1])
            self.mainLayout.lineEdit_singlePhOptFreq.setText(self.configArray[2][2])
            self.mainLayout.lineEdit_singlePhOptPulses.setText(self.configArray[2][3])
            self.mainLayout.lineEdit_singlePhAcqFreq.setText(self.configArray[2][4])
            self.mainLayout.lineEdit_singlePhAcqPulses.setText(self.configArray[2][5])

            # -------------------------
            # Intense LED tab
            self.mainLayout.lineEdit_highIntensVoltageLED_1.setText(self.configArray[3][0])
            self.mainLayout.lineEdit_highIntensOptFreq.setText(self.configArray[3][1])
            self.mainLayout.lineEdit_highIntensOptPulses.setText(self.configArray[3][2])
            self.mainLayout.lineEdit_highIntensAcqFreq.setText(self.configArray[3][3])
            self.mainLayout.lineEdit_highIntensAcqPulses.setText(self.configArray[3][4])

            # -------------------------
            # Low LED tab
            self.mainLayout.lineEdit_channelOfLED_2.setText(self.configArray[4][0])
            self.mainLayout.lineEdit_channelOfLED_3.setText(self.configArray[4][1])
            self.mainLayout.lineEdit_lowIntensVoltageLEDs.setText(self.configArray[4][2])
            self.mainLayout.lineEdit_lowIntensVoltageFactor.setText(self.configArray[4][3])
            self.mainLayout.lineEdit_lowIntensAcqFreq.setText(self.configArray[4][4])
            self.mainLayout.lineEdit_lowIntensAcqPulses.setText(self.configArray[4][5])

            # -------------------------
            # Linearity tab
            self.mainLayout.lineEdit_linearityVoltageFactor.setText(self.configArray[5][0])
            self.mainLayout.lineEdit_numberOfColpi.setText(self.configArray[5][1])
            self.mainLayout.lineEdit_numberOfSteps.setText(self.configArray[5][2])
            self.mainLayout.lineEdit_incrementLED_2.setText(self.configArray[5][3])
            self.mainLayout.lineEdit_incrementLED_3.setText(self.configArray[5][4])
            self.mainLayout.lineEdit_initialVoltageLED_2.setText(self.configArray[5][5])
            self.mainLayout.lineEdit_initialVoltageLED_3.setText(self.configArray[5][6])
            self.mainLayout.lineEdit_linearityAcqFreq.setText(self.configArray[5][7])

            # -------------------------
            # HV identities
            index = int(self.configArray[0][6])

            for row in range(self.mainLayout.tableWidget_inputID.rowCount()):
                for col in range(self.mainLayout.tableWidget_inputID.columnCount()):
                    #
                    edit = ((index == 1) or ((index == 0) and (row == 0)))
                    #
                    if (len(self.configArray) > (row +6)):
                        value = self.configArray[row +6][col]
                    else:
                        value = ""
                    #
                    self.fillInputIDTable(row, col, value, edit=edit)
        except:
            pass


    def initialSetup(self):
        # Clean the history of execution
        self.mainLayout.listWidget_logView.clear()

        # -------------------------
        # Table to receive (input) identities of High Voltage sources (CAEN)
        # Set column width...
        self.mainLayout.tableWidget_inputID.setColumnWidth(0, 80)       # HV model
        self.mainLayout.tableWidget_inputID.setColumnWidth(1, 35)       # S/N
        self.mainLayout.tableWidget_inputID.setColumnWidth(2, 125)      # f(x) = a.x + b (a)
        self.mainLayout.tableWidget_inputID.setColumnWidth(3, 110)      # f(x) = a.x + b (b)

        self.changedNumberChannels(index=0)

        # -------------------------
        # Table to display monitoring information (voltage and current)
        # Clean table values...
        for row in range(self.mainLayout.tableWidget_table.rowCount()):
            for col in range(self.mainLayout.tableWidget_table.columnCount()):
                self.mainLayout.tableWidget_table.setItem(row, col, QTableWidgetItem(""))

        # Set default parameters values for configuration
        # -------------------------
        # Initial setup tab
        self.mainLayout.lineEdit_initialVoltage.setText("1200")
        self.mainLayout.lineEdit_maxVoltageError.setText("0.02")
        self.mainLayout.lineEdit_voltageFactor.setText("2.0")
        self.mainLayout.lineEdit_maxVMonError.setText("0.03")
        self.mainLayout.lineEdit_currentFactor.setText("((2100/2.5)*(100/66975))")
        #self.mainLayout.lineEdit_maxIMonError.setText("0.03")
        self.mainLayout.lineEdit_maxIMonError.setText("10.0")
        self.comboBox_numberOfChannels.setCurrentIndex(0)
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

        # -------------------------
        # Button images
        saveIcon = QIcon("./icons/save.png")
        openIcon = QIcon("./icons/open.png")

        self.mainLayout.pushButton_save.setIcon(saveIcon)
        self.mainLayout.pushButton_open.setIcon(openIcon)


    def informExecution(self, message=""):
        self.mainLayout.listWidget_logView.addItem(datetime.now().strftime('%d/%m/%Y %H:%m:%S') + " - " + message)

    #@pyqtSlot()
    def fillTable(self, row, col, value):
        self.mainLayout.tableWidget_table.setItem(row, col, QTableWidgetItem(str(value)))

    def fillInputIDTable(self, row, col, value, edit=True):
        # --------------------------
        item = QTableWidgetItem(str(value))
        if (edit):
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
        else:
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        self.mainLayout.tableWidget_inputID.setItem(row, col, item)

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
