#!/usr/bin/env python3.4
"""
Control all the communicattion with Linduino, sending to them the commands necessary to control DAQ and also control auxiliary softwares that control Wavedump.
"""
import serial
import subprocess
import os

from time import sleep

from PyQt5.QtCore import pyqtSignal, QObject

"""
Abstraction of Linduino board
"""
class Linduino():
    def __init__(self):
        # Set default parameters configuration
        self.port = "/dev/ttyUSB0"
        self.rate = 115200
        # Initiate USB connection to Linduino
        try:
            self.connection = serial.Serial(self.port, self.rate)
            # Wait a while for Linduino initialization...
            sleep(2)
        except:
            self.connection = None
            print("Error connecting to Linduino!")
            pass

    def sendCommand(self, command=""):
        command = str(command)
        listOfCommands = command.split(";")

        if (self.connection):
            for cmd in listOfCommands:
                try:
                    # Encode the command to bytes and send it
                    self.connection.write(str.encode(str(cmd)))
                    # After each individual command a terminator should be send
                    self.connection.write(b'\n')
                except:
                   print("Error sending command: %s!" %(cmd))
                   pass
        else:
            print("No connection stablished! Impossible to send commands...")


    def readReturn(self):
        if (self.connection):
            # Read everything in the input buffer
            returnedMessage = self.connection.read(self.connection.inWaiting())
            # Decode received bytes
            returnedMessage = returnedMessage.decode('utf-8')
        else:
            returnedMessage = None
            print("No connection stablished! Impossible to read buffer...")

        return returnedMessage


    def getConnection(self):
        return self.connection


    def reconnect(self):
        # Try to connect to Linduino
        try:
            self.connection = serial.Serial(self.port, self.rate)
            # Wait a while for Linduino initialization...
            sleep(2)
        except:
            self.connection = None
            print("Error connecting to Linduino!")
            pass


    def closeConnection(self):
        if (self.connection):
            self.connection.close()


    def __del__(self):
        if (self.connection):
            self.closeConnection()


"""
Abstraction of Small Photo Multiplier Tube (SPMT) to controll all the process
"""
class SmallPhotoMultiplierTubeController():
    def __init__(self):
        # Initialize attributes
        self.numberOfChannels = 8               # Default 8 channels, from 0 to 7
        self.debug = False                      # Default is NO debug, False
        # Managed files
        # .log
        self.errorDacFileName                   = "./logs/ERROR_DAC_UNICAMP.log"            # File name of error log when DAC presents problem
        self.errorModuleFileName                = "./logs/ERROR_MODULE_UNICAMP.log"         # File name of error log when Module presents problem
        self.errorPmtFileName                   = "./logs/ERROR_PMT_UNICAMP.log"            # File name of error log when PMT presents problem
        # .cfg
        self.darkCountGaussFileName             = "./Parametri_gaussiana_dark.cfg"          # File of configuration of gaussian for dark count
        self.voltagesGainTableFileName          = "./tabella_tensioni_guadagno_7*10^5.cfg"  # File of configuration of voltages gain
        # .txt
        self.comunicaWaveDumpFileName           = "./comunicazioneW.txt"                    # File to help contacting WaveDump modified and control it
        self._10PercentFileName                 = "./Cerca.txt"                             # File with result of 10Percento program execution
        self.searchFileName                     = "./Continua.txt"                          # File with result of Ricerca program execution
        self.singlePhotoelectronFileName        = "./singolo.txt"
        self.configLinearity                    = "./datilin.txt"
        self.waveOriginFileName                 = "./wave_%d.txt"
        self.waveSinglePhotoelectronFileName    = "./wave_%d_ph.txt"
        self.waveIntenseLEDFileName             = "./wave_%d_LED_high.txt"
        self.waveLowLEDFileName                 = "./wave_%d_LED_low.txt"

        # Instantiate all objects needed to controll SPMT
        self.linduinoObj = Linduino()


    def getNumberOfChannels(self):
        return self.numberOfChannels


    def setNumberOfChannels(self, number=1):
        if (number and number >= 1):
            self.numberOfChannels = number
        else:
            print("Invalid number of channels...")


    def isDebug(self):
        return self.debug


    def setDebug(self, debug=False):
        self.debug = debug


    def setVoltageToAllChannels(self, voltage=0):
        for channel in range(self.getNumberOfChannels()):
            self.setVoltageToOneChannel(channel, voltage)


    def setVoltageToAllChannelsByArray(self, voltagesArray=[]):
        status = True

        try:
            if (len(voltagesArray) == self.getNumberOfChannels()):
                for channel in range(self.getNumberOfChannels()):
                    self.setVoltageToOneChannel(channel, voltagesArray[channel])
            else:
                status = False
                print("Inconsistent number of voltage values for all selected channels...")
        except:
            status = False
            print("Exception when trying to set new voltages....")
            pass

        return status

    def setVoltageToOneChannel(self, channel, voltage=0):
        # -----------------------------------------------------------------
        # This depends on Linduino program;
        # -----------------------------------------------------------------
        # At the moment, options are:
        #     '1'-Select DAC:
        #         -> Select DAC (channel) to operate on (1-15, or 16 for All): <channel>
        #     '3'-Write and update DAC:
        #         -> Type 1 to enter voltage, 2 to enter code:
        #             -> '1' (voltage)
        #                 -> Enter desired DAC output voltage:
        #                     -> 99.999;
        # -----------------------------------------------------------------
        # So, '1'-> '3' -> '1' -> '99.999'; we send it to Linduino separating 
        # by semicolons to indicate each individual command; at the end of each
        # command a terminator should be send.
        # -----------------------------------------------------------------
        self.linduinoObj.sendCommand("1;" + str(channel) + ";3;1;" + str(voltage))
        # Wait for the command to be executed and response has been sent
        sleep(0.5)

        # Read the return
        returnedMessage = self.linduinoObj.readReturn()

        if (self.isDebug()):
            # Print just for debug pourposes...
            print(returnedMessage)


    def setMuxToAllChannels(self, enable=False):
        listOfVoltagesRead = []

        for channel in range(self.getNumberOfChannels()):
            listOfVoltagesRead.append(self.setMuxToOneChannel(channel, enable))

        if (self.isDebug()):
            print("---------")
            print("List of voltages read: ", listOfVoltagesRead)

        return listOfVoltagesRead


    def setMuxToOneChannel(self, channel=None, enable=False):
        # -----------------------------------------------------------------
        # This depends on Linduino program;
        # -----------------------------------------------------------------
        # At the moment, options are:
        #     '9'-Set Mux:
        #         -> '0'-Disable Mux;
        #         -> '1'-Enable Mux:
        #             -> Select MUX channel(0-CH0, 1-CH1,...15-CH15):
        #                 -> 0-15;
        # -----------------------------------------------------------------
        # So, '9'-> '0' or '1' -> (if '1') : -> 0-15; we send it to Linduino separating 
        # by semicolons to indicate each individual command; at the end of each
        # command a terminator should be send.
        # -----------------------------------------------------------------
        if (enable):
            self.linduinoObj.sendCommand("9;" + str(int(enable)) + ";" + str(channel))
        else:
            self.linduinoObj.sendCommand("9;" + str(int(enable)))

        # Wait for the command to be executed and response has been sent
        # During tests, the lowest time to get info was 0.9 sec.
        sleep(1.0)

        # Read the return
        returnedMessage = self.linduinoObj.readReturn()

        if (self.isDebug()):
            # Print just for debug pourposes...
            print(returnedMessage)

        # When enabling MUX we get a voltage for selected channel
        voltageRead = -1.0

        if (enable):
            # After enable MUX, Linduino returns read voltage for selected channel
            listOfReturn = returnedMessage.split('\r\n')
            try:
                # Returned voltage is in the 5th line, or index "4"
                voltageRead = round(float(listOfReturn[4]), 3)
                if (self.isDebug()):
                    print("---------")
                    print("Voltage read: ", voltageRead)
            except IndexError:
                print("Error when getting voltage for channel %s..." % str(channel))

        return voltageRead


    def validateDACVoltages(self, voltagesArray, reference, maxError=0.02):
        errorFile = open(self.errorDacFileName, "w")
        validVoltages = True

        try:
            for index, voltage in enumerate(voltagesArray):
                if (abs(voltage - reference) > maxError):
                    errorMessage = ("Channel %d with error margin for VSet grater than %.3f.  Expected voltage: %.3f, but read: %.3f.\n" % (index, maxError, reference, voltage))
                    # Save information into file
                    errorFile.write(errorMessage)
                    validVoltages = False

                    if (self.isDebug()):
                        print(errorMessage)
        except:
            validVoltages = False
            print("Exception when validating voltages!")
            pass

        errorFile.close()

        return validVoltages


    def readMonitorsOfAllChannels(self):
        listOfMonitorsRead = []

        # Start monitor procedure
        self.startMonitorFunction()

        for channel in range(self.getNumberOfChannels()):
            listOfMonitorsRead.append(self.readMonitorsOfOneChannel(channel))

        if (self.isDebug()):
            print("---------")
            print("List of monitors (IMon and VMon) read: ", listOfMonitorsRead)

        # Stop monitor procedure
        self.stopMonitorFunction()

        return listOfMonitorsRead


    def startMonitorFunction(self):
        # -----------------------------------------------------------------
        # Start the function of IMon and VMon monitoring.
        # -----------------------------------------------------------------
        # This depends on Linduino program;
        # -----------------------------------------------------------------
        # At the moment, options are:
        #     '17'-Multiplex Lettura:
        # -----------------------------------------------------------------
        # So, '17'-> ...; we send it to Linduino separating 
        # by semicolons to indicate each individual command; at the end of each
        # command a terminator should be send.
        # -----------------------------------------------------------------
        self.linduinoObj.sendCommand("17")

        # Wait for the command to be executed and response has been sent
        # Empirical value to wait before start IMon and VMon read function....
        sleep(3)

        # Read the return
        returnedMessage = self.linduinoObj.readReturn()

        if (self.isDebug()):
            # Print just for debug pourposes...
            print(returnedMessage)

    def stopMonitorFunction(self):
        # -----------------------------------------------------------------
        # Start the function of IMon and VMon monitoring.
        # -----------------------------------------------------------------
        # This depends on Linduino program;
        # -----------------------------------------------------------------
        # At the moment, options are:
        #     '9'-Exit Multiplex Lettura:
        # -----------------------------------------------------------------
        # So, '9'-> ...; we send it to Linduino separating 
        # by semicolons to indicate each individual command; at the end of each
        # command a terminator should be send.
        # -----------------------------------------------------------------
        self.linduinoObj.sendCommand("9")

        # Wait for the command to be executed and response has been sent
        # Empirical value to wait before start IMon and VMon read function....
        sleep(0.5)

        # Read the return
        returnedMessage = self.linduinoObj.readReturn()

        if (self.isDebug()):
            # Print just for debug pourposes...
            print(returnedMessage)


    def readMonitorsOfOneChannel(self, channel):
        # Send command to get information of one channel
        self.linduinoObj.sendCommand(str(channel))

        # Wait for the command to be executed and response has been sent
        sleep(0.5)

        # Read the return
        returnedMessage = self.linduinoObj.readReturn()

        if (self.isDebug()):
            # Print just for debug pourposes...
            print(returnedMessage)

        listOfReturn = returnedMessage.split('\n')

        try:
            # Pair of IMon and VMon is returned in the first line, or index "0", and they are separated by a space ' '
            monitorRead = listOfReturn[0].split(' ')
            if (self.isDebug()):
                print("---------")
                print("Monitor (IMon and VMon) read: ", monitorRead)
        except IndexError:
            print("Error when getting monitor IMon and VMon for channel %s..." % str(channel))

        return monitorRead


    def validateModuleMonitor(self, voltagesArray, monitorArray, vFactor=2.0, iFactor=1.2541993281, maxVMonError=0.03, maxIMonError=0.03):
        errorModFile = open(self.errorModuleFileName, "w")
        errorPmtFile = open(self.errorPmtFileName, "w")

        validMonitors = True

        try:
            if (len(voltagesArray) == len(monitorArray)):
                for index, (monitor, voltage) in enumerate(zip(monitorArray, voltagesArray)):
                    # Each cell of 'monitorArray' is an array with IMon at index '0' and VMon at index '1'
                    # ----------------------------------------------------------------------------
                    # Validate IMon...
                    iMon = round(float(monitor[0]), 3)
                    # 
                    iReference = round(float(voltage) * iFactor, 3)

                    if (abs(iMon - iReference)/iReference > maxIMonError):
                        errorMessage = ("Channel %d with error margin for IMon (PMT) grater than %.3f.  Expected iMon: %.3f, but read: %.3f.\n" % (index, maxIMonError, iReference, iMon))
                        # Save information into file
                        errorPmtFile.write(errorMessage)
                        validMonitors = False

                        if (self.isDebug()):
                            print(errorMessage)

                    # ----------------------------------------------------------------------------
                    # Validate VMon...
                    vMon = round(float(monitor[1]), 3)
                    # 
                    vReference = round(float(voltage) * vFactor, 3)

                    if (abs(vMon - vReference)/vReference > maxVMonError):
                        errorMessage = ("Channel %d with error margin for VMon (HV module) grater than %.3f.  Expected vMon: %.3f, but read: %.3f.\n" % (index, maxVMonError, vReference, vMon))
                        # Save information into file
                        errorModFile.write(errorMessage)
                        validMonitors = False

                        if (self.isDebug()):
                            print(errorMessage)

            else:
                validMonitors = False
                print("Error when validating monitors, number of informed values does not match!")
        except:
            validMonitors = False
            print("Exception when validating monitors!")
            pass

        errorModFile.close()
        errorPmtFile.close()

        return validMonitors


    def storeLinearityConfiguration(self, numberOfColpi=30, numberOfSteps=50):
        status = True

        try:
            fileLinearity = open(self.configLinearity, "w")

            fileLinearity.write("Numero colpi: " + str(numberOfColpi) + "\n")
            fileLinearity.write("Numero cicli: " + str(numberOfSteps) + "\n")

            fileLinearity.close()
        except:
            status = False

            if (fileLinearity):
                fileLinearity.close()

            print("Exception when trying to save configuration of linearity processing...")
            pass

        return status


    def storeVoltagesForSinglePhotoelectron(self, voltagesArray, voltageLowLED, voltageFactor=840.0):
        status = True

        try:
            if (len(voltagesArray) == self.getNumberOfChannels()):
                fileSinglePh = open(self.singlePhotoelectronFileName, "w")

                fileSinglePh.write("Tensioni singolo fotoelettrone: ")

                for voltage in voltagesArray:
                    fileSinglePh.write(str(round((voltageFactor * voltage), 2)) + " ")

                # line-break
                fileSinglePh.write('\n')
                fileSinglePh.write("Tensioni basse luce LED: ")

                for channel in range(self.getNumberOfChannels()):
                    fileSinglePh.write(str(round((voltageLowLED * voltage), 2)) + " ")

                fileSinglePh.close()
            else:
                status = False

                if (fileSinglePh):
                    fileSinglePh.close()

                print("Inconsistent number of elements in list of voltages read regarding the number of channels to process...")
        except:
            status = False

            if (fileSinglePh):
                fileSinglePh.close()

            print("Exception when trying to save voltages for single photoelectron...")
            pass

        return status


    def callWaveDump(self):
        status = True

        if (self.isDebug()):
            print("---------")
            print("Calling WaveDump...")

        try:
            subprocess.Popen(["/home/spmt/Documents/TorinoGroup/Wavedump/src/wavedump", "WaveDumpConfig.txt"])
            sleep(1)
        except:
            print("Error when trying to call WaveDump...")
            status = False
            pass

        return status


    def callWaveDumpAndTriggerDigitizer(self, frequency, numberOfPulses):
        status = True

        # Inform WaveDump to acquire using comunication file
        status = status and self.startWaveDumpAcquisition()
        
        # Call WaveDump program
        status = status and self.callWaveDump()

        # Call Trigger
        status = status and self.triggerDigitizer(frequency=frequency, numberOfPulses=numberOfPulses)

        # Inform WaveDump to stop acquisition and close
        status = status and self.stopWaveDumpAcquisition()

        return status


    def triggerDigitizer(self, frequency, numberOfPulses):
        status = True

        try:
            interval = 1000.0/frequency

            # -----------------------------------------------------------------
            # This depends on Linduino program;
            # -----------------------------------------------------------------
            # At the moment, options are:
            #     '16'-Loop trigger:
            # -----------------------------------------------------------------
            # So, '16'-> ...; we send it to Linduino separating 
            # by semicolons to indicate each individual command; at the end of each
            # command a terminator should be send.
            # -----------------------------------------------------------------
            # tempo0 (delay HIGH signal)
            # tempo1 (delay LOW signal)
            # tempo2 (n_impulsi, number of pulses)
            # tempo3 (n_cicli, number of cycles)
            # tempo4 (ritardo; delay between pulses)
            # -----------------------------------------------------------------
            #self.linduinoObj.sendCommand("16;" + str(interval) + ";0;" + str(numberOfPulses) + ";1;0")
            self.linduinoObj.sendCommand("16;" + str(interval) + ";" + str(interval) + ";" + str(numberOfPulses) + ";1;0")

            # Wait for the command to be executed and response has been sent
            # Empirical value to wait before start IMon and VMon read function....
            sleep(0.5)

            # Read the return
            returnedMessage = self.linduinoObj.readReturn()

            if (self.isDebug()):
                # Print just for debug pourposes...
                print(returnedMessage)

            while (True):
                returnedMessage = self.linduinoObj.readReturn()

                if (returnedMessage):
                    listMessages = returnedMessage.split('\n')
                    # print(listMessages)

                    if (listMessages[0] == "Fine trigger"):
                        if (self.isDebug()):
                            # Print just for debug pourposes...
                            print("---------")
                            print(listMessages[0])
                        break

                sleep(0.5)
        except:
            print("Error when trying to trigger digitizer...")
            status = False
            pass

        return status

    def startWaveDumpAcquisition(self):
        status = True
        try:
            fileComunica = open(self.comunicaWaveDumpFileName, "w")
            fileComunica.write("a")
            fileComunica.close()

            if (self.isDebug()):
                print("---------")
                print("Inform WaveDump to start acquisition...")
        except:
            status = False

            if (fileComunica):
                fileComunica.close()

            print("Error writing START to file of comunication to WaveDump: %s..." % self.comunicaWaveDumpFileName)
            pass

        return status


    def stopWaveDumpAcquisition(self):
        status = True

        try:
            fileComunica = open(self.comunicaWaveDumpFileName, "w")
            fileComunica.write("s")
            fileComunica.close()
            # ----------
            sleep(0.01)

            fileComunica = open(self.comunicaWaveDumpFileName, "w")
            fileComunica.write("q")
            fileComunica.close()

            if (self.isDebug()):
                print("---------")
                print("Inform WaveDump to stop acquisition and close...")
        except:
            status = False

            if (fileComunica):
                fileComunica.close()

            print("Error writing STOP to file of comunication to WaveDump: %s..." % self.comunicaWaveDumpFileName)
            pass

        return status


    """
    Run Fondo.exe
    """
    def callDarkCountProcess(self):
        status = True

        if (self.isDebug()):
            print("---------")
            print("Calling Fondo.exe...")
            print("---------")

        try:
            # Remove previous configuration file for dark count
            if (os.path.exists(self.darkCountGaussFileName)):
                os.remove(self.darkCountGaussFileName)

            subprocess.Popen("./Fondo.exe")

            # Wait until a new dark count gaussian configuration file is created
            while (True):
                if (os.path.exists(self.darkCountGaussFileName)):
                    break

            # Just wait while more
            sleep(1)

            if (self.isDebug()):
                print("---------")
                print("End of processing files by Fondo.exe")
                print("---------")

        except:
            print("Error calling Fondo.exe...")
            status = False
            pass

        return status


    """
    Run 10Percento.exe
    """
    def call10PercentProcess(self):
        status = True

        if (self.isDebug()):
            print("---------")
            print("Calling 10Percento.exe...")
            print("---------")

        try:
            # Remove previous configuration file for 10 percent
            if (os.path.exists(self._10PercentFileName)):
                os.remove(self._10PercentFileName)

            subprocess.Popen("./10Percento.exe")

            # Wait until a new 10 percent result file is created
            while (True):
                if (os.path.exists(self._10PercentFileName)):
                    break

            # Just wait while more
            sleep(1)

            if (self.isDebug()):
                print("---------")
                print("End of processing files by 10Percento.exe")
                print("---------")

        except:
            print("Error calling 10Percento.exe...")
            status = False
            pass

        return status


    """
    Run Ricerca.exe
    """
    def callSearchProcess(self):
        status = True

        if (self.isDebug()):
            print("---------")
            print("Calling Ricerca.exe...")
            print("---------")

        try:
            # Remove previous configuration file for ricerca
            if (os.path.exists(self.searchFileName)):
                os.remove(self.searchFileName)

            subprocess.Popen("./Ricerca.exe")

            # Wait until a new ricerca result file is created
            while (True):
                if (os.path.exists(self.searchFileName)):
                    break

            # Just wait while more
            sleep(1)

            if (self.isDebug()):
                print("---------")
                print("End of processing files by Ricerca.exe")
                print("---------")

        except:
            print("Error calling Ricerca.exe...")
            status = False
            pass

        return status


    """
    Run Single_ph.exe
    """
    def callSinglePhotoelectronProcess(self):
        status = True

        if (self.isDebug()):
            print("---------")
            print("Calling Single_ph.exe...")
            print("---------")

        try:
            # Remove previous configuration file for Single Ph
            if (os.path.exists(self.voltagesGainTableFileName)):
                os.remove(self.voltagesGainTableFileName)

            subprocess.Popen("./Single_ph.exe")

            # Wait until a new Single Ph result file is created
            while (True):
                if (os.path.exists(self.voltagesGainTableFileName)):
                    break

            # Just wait while more
            sleep(1)

            if (self.isDebug()):
                print("---------")
                print("End of processing files by Single_ph.exe")
                print("---------")

        except:
            print("Error calling Single_ph.exe...")
            status = False
            pass

        return status


    """
    Run Linearity.exe
    """
    def callLinearityProcess(self):
        status = True

        if (self.isDebug()):
            print("---------")
            print("Calling Linearity.exe...")
            print("---------")

        try:
            subprocess.Popen("./Linearity.exe")

            # XXX - This should be enhanced... is there a way to know when Linearity.exe is finished?
            # Wait a while ()
            sleep(5)

            if (self.isDebug()):
                print("---------")
                print("Linearity.exe was started and could be still runnning... if so, wait a while!")
                print("---------")

        except:
            print("Error calling Linearity.exe...")
            status = False
            pass

        return status


    def read10PercentResultContent(self):
        result = None

        try:
            fileResult = open(self._10PercentFileName, "r")
        except FileNotFoundError:
            print("Error when loading 10Percento.exe results file...")
            return result

        try:
            # It should have just one line
            content = fileResult.readline()
            result = int(content.split(' ')[0])
        except:
            print("Error in content of 10Percento.exe results file...")
            return result

        return result


    def readSearchResultContent(self):
        result = None

        try:
            fileResult = open(self.searchFileName, "r")
        except FileNotFoundError:
            print("Error when loading Ricerca.exe results file...")
            return result

        try:
            # It should have just one line
            content = fileResult.readline()
            result = int(content.split(' ')[0])
        except:
            print("Error in content of Ricerca.exe results file...")
            return result

        return result


    def readVoltagesCalculatedBySinglePhotoelectron(self, voltagesArray, voltageFactor=1.190476e-03):
        status = True

        try:
            fileGainConfig = open(self.voltagesGainTableFileName, "r")

            linesOfGainFile = fileGainConfig.readlines()

            for index, voltage in enumerate(voltagesArray):
                try:
                    voltage = round(float(linesOfGainFile[(index*2) +1].split(' ')[2]), 3)
                    voltagesArray[index] = round((voltage * voltageFactor), 3)
                except IndexError:
                    status = False
                    print("Exception when trying to read gain voltage for channel %d..." % index)
                    pass

            fileGainConfig.close()
        except:
            status = False

            if (fileGainConfig):
                fileGainConfig.close()

            print("Exception when processing voltages gain table file, %s..." % self.voltagesGainTableFileName)
            pass

        return voltagesArray, status


    def renameWaveFilesForSinglePhotoelectron(self):
        for channel in range(self.getNumberOfChannels()):
            try:
                if (os.path.exists(self.waveOriginFileName % channel)):
                    os.rename(self.waveOriginFileName % channel, self.waveSinglePhotoelectronFileName % channel)
                else:
                    print("Error, file not found: %s..." % (self.waveOriginFileName % channel))
            except:
                print("Exception when renaming wave files, at channel %d..." % channel)
                pass


    def renameWaveFilesForIntenseLED(self):
        for channel in range(self.getNumberOfChannels()):
            try:
                if (os.path.exists(self.waveOriginFileName % channel)):
                    os.rename(self.waveOriginFileName % channel, self.waveIntenseLEDFileName % channel)
                else:
                    print("Error, file not found: %s..." % (self.waveOriginFileName % channel))
            except:
                print("Exception when renaming wave files, at channel %d..." % channel)
                pass


    def renameWaveFilesForLowLED(self):
        for channel in range(self.getNumberOfChannels()):
            try:
                if (os.path.exists(self.waveOriginFileName % channel)):
                    os.rename(self.waveOriginFileName % channel, self.waveLowLEDFileName % channel)
                else:
                    print("Error, file not found: %s..." % (self.waveOriginFileName % channel))
            except:
                print("Exception when renaming wave files, at channel %d..." % channel)
                pass


    def closeConnection(self):
        if (self.linduinoObj):
            self.linduinoObj.closeConnection()


    def __del__(self):
        self.closeConnection()


"""
Orchestrator()
"""
class Orchestrator(QObject):
    # ----------------------------------------------
    # Signals to communicate with UI
    informExecution = pyqtSignal(str)
    fillTable = pyqtSignal(int, int, str)

    def __init__(self):
        QObject.__init__(self)

        self.activeDebugging = True

        # -------------------------------------------
        # Local attributes - Values for production
        self.initialVoltage         = 1.75
        self.maxVoltageError        = 0.02
        self.voltageFactor          = 2.0       # 5.1
        self.currentFactor          = ((2100/2.5)*(100/66975))
        self.maxVMonError           = 0.03      # 0.7
        self.maxIMonError           = 0.03      # 0.5
        self.darkCountFreq          = 100
        self.darkCountPulses        = 100000
        self.singlePhOptFreq        = 100
        self.singlePhOptPulses      = 5000
        self.singlePhAcqFreq        = 100
        self.singlePhAcqPulses      = 100000
        self.singlePhVoltageLED_1   = 2.5
        self.highIntensVoltageLED_1 = 7.0
        self.highIntensOptFreq      = 10
        self.highIntensOptPulses    = 150
        self.highIntensAcqFreq      = 10
        self.highIntensAcqPulses    = 600
        self.lowIntensVoltageLEDs   = 1.25
        self.lowIntensVoltageFactor = (2100.0/2.5)
        self.lowIntensAcqFreq       = 10
        self.lowIntensAcqPulses     = 600
        self.channelOfLED_1         = 8
        self.channelOfLED_2         = 9
        self.channelOfLED_3         = 10
        self.linearityVoltageFactor = (2.5/2100.0)
        self.numberOfColpi          = 30
        self.numberOfSteps          = 50
        self.voltageLED_2           = 0
        self.voltageLED_3           = 0
        self.incrementLED_2         = 0.15
        self.incrementLED_3         = 0.1
        self.initialVoltageLED_2    = 4.0
        self.initialVoltageLED_3    = 4.0
        self.linearityAcqFreq       = 10

        # Instantiate an object of SMPT Controller
        self.spmtControllerObj = SmallPhotoMultiplierTubeController()

    # ----------------------------------------------------------------
    def setDebug(self, debug=True):
        self.activeDebugging = debug

    # ----------------------------------------------------------------
    def calcNewVoltageLED(self, voltageLED, a, b, c, factor1, factor2):
        if ((a == 2) and (c != 1)):
            voltageLED = voltageLED + ((factor1) / (factor2**b))

        if ((a == 2) and (c == 1)):
            b += 1
            voltageLED = voltageLED + ((factor1) / (factor2**b))

        if ((a == 1) and (c != 2)):
            voltageLED = voltageLED - ((factor1) / (factor2**b))

        if ((a == 1) and (c != 2)):
            voltageLED = voltageLED - ((factor1) / (factor2**b))

        return voltageLED, a, b, c


    # ----------------------------------------------------------------
    def abortProgram(self, executionStep="unknow"):
            print("----------------------------------------------------------------")
            print("Error when %s.  Aborting the program..." % (executionStep))
            print("----------------------------------------------------------------")
            self.informExecution.emit("----------------------------------------------------------------")
            self.informExecution.emit("Error when %s.  Aborting the program..." % (executionStep))

            if (self.spmtControllerObj):
                # Turn the voltages off...
                self.spmtControllerObj.setVoltageToAllChannels(voltage=0)
                # Close connection, if any
                self.spmtControllerObj.closeConnection()


    """
    Execute()
    """
    def executeProgram(self):
        print("----------------------------------------------------------------")
        print("-:- Start of program -:-")
        print("----------------------------------------------------------------")
         # Only for commissioning
        self.spmtControllerObj.setDebug(self.activeDebugging)

        print("----------------------------------------------------------------")
        print("-:- Set initial voltages -:-")
        print("----------------------------------------------------------------")
        # --------------------------------------------------------------------
        # Initialize all voltages of operational channels
        self.spmtControllerObj.setVoltageToAllChannels(voltage=self.initialVoltage/2)
        self.informExecution.emit("Setting initial voltages to: %.3f..." % float(self.initialVoltage/2))

        print("----------------------------------------------------------------")
        print("-:- Enable MUX and get current Voltages -:-")
        print("----------------------------------------------------------------")
        # --------------------------------------------------------------------
        # Enable MUX and check voltages...
        listOfVoltagesRead = self.spmtControllerObj.setMuxToAllChannels(enable=True)
        self.informExecution.emit("Getting voltages from MUX...")

        # Emit signal to inform UI table...
        for index, voltage in enumerate(listOfVoltagesRead):
            self.fillTable.emit(index, 0, str(round(float(voltage), 3)))

        print("----------------------------------------------------------------")
        print("-:- Disble MUX -:-")
        print("----------------------------------------------------------------")
        # --------------------------------------------------------------------
        # Disbale MUX...
        self.spmtControllerObj.setMuxToOneChannel()
        self.informExecution.emit("Disabling MUX...")

        print("----------------------------------------------------------------")
        print("-:- Validate current voltages -:-")
        print("----------------------------------------------------------------")
        # --------------------------------------------------------------------
        # Validate read voltages
        self.informExecution.emit("Validating voltages...")
        validVoltages = self.spmtControllerObj.validateDACVoltages(voltagesArray=listOfVoltagesRead, reference=self.initialVoltage/2, maxError=self.maxVoltageError)

        if (not validVoltages):
            self.abortProgram(executionStep="validating DAC voltages")
            return -1
        else:
            print("Voltages OK!")
            self.informExecution.emit("Voltages OK!")

        print("----------------------------------------------------------------")
        print("-:- Read IMon and VMon -:-")
        print("----------------------------------------------------------------")
        # --------------------------------------------------------------------
        # Read IMon and VMon...
        self.informExecution.emit("Reading monitors (IMon and VMon)...")
        listOfMonitorsRead = self.spmtControllerObj.readMonitorsOfAllChannels()

        # Emit signal to inform UI table...
        for index, (monitor, voltage) in enumerate(zip(listOfMonitorsRead, listOfVoltagesRead)):
            # VMon
            self.fillTable.emit(index, 1, str(round(float(monitor[1]), 3)))
            # IMon
            self.fillTable.emit(index, 2, str(round(float(monitor[0]), 3)))

        print("----------------------------------------------------------------")
        print("-:- Validate IMon and VMon -:-")
        print("----------------------------------------------------------------")
        # --------------------------------------------------------------------
        # Validate IMon and VMon...
        self.informExecution.emit("Validating monitors (IMon and VMon)...")
        validMonitor = self.spmtControllerObj.validateModuleMonitor(voltagesArray=listOfVoltagesRead, monitorArray=listOfMonitorsRead, vFactor=self.voltageFactor, iFactor=self.currentFactor, maxVMonError=self.maxVMonError, maxIMonError=self.maxIMonError)

        if (not validMonitor):
            self.abortProgram(executionStep="validating IMon (PMT) and VMon (module HV)")
            return -1
        else:
            print("IMon and VMon OK!")
            self.informExecution.emit("IMon and VMon OK!")

        print("----------------------------------------------------------------")
        print("-:- Dark count -:-")
        print("----------------------------------------------------------------")
        # --------------------------------------------------------------------
        # Dark count...
        self.informExecution.emit("Acquiring and processing dark count...")
        triggered = self.spmtControllerObj.callWaveDumpAndTriggerDigitizer(frequency=self.darkCountFreq, numberOfPulses=self.darkCountPulses)

        if (triggered):
            # Then process (Dark Count) output files of WaveDump
            self.spmtControllerObj.callDarkCountProcess()
        else:
            self.abortProgram(executionStep="triggering digitizer and running WaveDump")
            return -1

        print("----------------------------------------------------------------")
        print("-:- Single photoelectron -:-")
        print("----------------------------------------------------------------")
        # --------------------------------------------------------------------
        # Single photoelectron...
        self.informExecution.emit("Acquiring and processing single photoelectron...")
        # --------------------------------------------------------------------
        # Initial values of control (auxiliary) parameters
        a = 0       # Stores the value returned by 10Percento.exe program;
        b = 0       # Stores returned value of 10Percento.exe program in previous execution;
        c = 0       # Each time the direction of increment/decrement of LED voltage is inverted, "b" is incremented,
                    #   then, next steps to increment/decrement LED voltage will be more thick;

        maximumTries = 10
        currentTry = 0

        while (True):
            # Inform details if debugging
            if (self.activeDebugging):
                print("---------")
                print("Setting voltage %.3f to LED 1..." % (self.singlePhVoltageLED_1/2))
                print("---------")

            # LED_1 is connected to channel 8, so, simply set voltage output to that channel
            self.spmtControllerObj.setVoltageToOneChannel(channel=self.channelOfLED_1, voltage=(self.singlePhVoltageLED_1/2))

            # ----------------------------------------------------------------
            # Trigger CAEN digitizer running WaveDump
            triggered = self.spmtControllerObj.callWaveDumpAndTriggerDigitizer(frequency=self.singlePhOptFreq, numberOfPulses=self.singlePhOptPulses)

            if (triggered):
                # Then process (10 Percent) output files of WaveDump
                self.spmtControllerObj.call10PercentProcess()
            else:
                self.abortProgram(executionStep="triggering digitizer and running WaveDump during single photoelectron measuring")
                return -1

            # ----------------------------------------------------------------
            # Logic to incread/decrease LED_1 intensity
            a = self.spmtControllerObj.read10PercentResultContent()

            # ---------
            if ((a == 0) or (currentTry >= maximumTries)):
                break

            # ---------
            self.singlePhVoltageLED_1, a, b, c = self.calcNewVoltageLED(self.singlePhVoltageLED_1, a, b, c, 0.2, 5)

            # ---------
            c = a

            # This is for instrumentation only
            currentTry += 1

        # --------------------------------------------------------------------
        # Acquire new WaveDump files with LED configured with 10 percent
        triggered = self.spmtControllerObj.callWaveDumpAndTriggerDigitizer(frequency=self.singlePhAcqFreq, numberOfPulses=self.singlePhAcqPulses)

        if (triggered):
            # Then rename files for single photoelectron
            self.spmtControllerObj.renameWaveFilesForSinglePhotoelectron()
        else:
            self.abortProgram(executionStep="triggering digitizer and running WaveDump to acquire waves at 10 percent")
            return -1

        print("----------------------------------------------------------------")
        print("-:- Intense LED light -:-")
        print("----------------------------------------------------------------")
        # --------------------------------------------------------------------
        # Intense LED light start...
        self.informExecution.emit("Acquiring and processing intense LED light...")
        # --------------------------------------------------------------------
        # Initial values of control (auxiliary) parameters
        a = 0       # Stores the value returned by 10Percento.exe program;
        b = 0       # Stores returned value of 10Percento.exe program in previous execution;
        c = 0       # Each time the direction of increment/decrement of LED voltage is inverted, "b" is incremented,
                    #   then, next steps to increment/decrement LED voltage will be more thick;

        maximumTries = 10
        currentTry = 0

        while (True):
            # Inform details if debugging
            if (self.activeDebugging):
                print("---------")
                print("Setting voltage %.3f to LED 1..." % (self.highIntensVoltageLED_1/2))
                print("---------")

            # LED_1 is connected to channel 8, so, simply set voltage output to that channel
            self.spmtControllerObj.setVoltageToOneChannel(channel=self.channelOfLED_1, voltage=(self.highIntensVoltageLED_1/2))

            # ----------------------------------------------------------------
            # Trigger CAEN digitizer running WaveDump
            triggered = self.spmtControllerObj.callWaveDumpAndTriggerDigitizer(frequency=self.highIntensOptFreq, numberOfPulses=self.highIntensOptPulses)

            if (triggered):
                # Then process Search ("Ricerca") output files of WaveDump
                self.spmtControllerObj.callSearchProcess()
            else:
                self.abortProgram(executionStep="triggering digitizer and running WaveDump during intense LED measuring")
                return -1

            # ----------------------------------------------------------------
            # Logic to incread/decrease LED_1 intensity
            a = self.spmtControllerObj.readSearchResultContent()

            # ---------
            if ((a == 0) or (currentTry >= maximumTries)):
                break

            # ---------
            self.highIntensVoltageLED_1, a, b, c = self.calcNewVoltageLED(self.highIntensVoltageLED_1, a, b, c, 0.5, 5)

            # ---------
            c = a

            # This is for instrumentation only
            currentTry += 1

        # --------------------------------------------------------------------
        # Acquire new WaveDump files with LED configured with high intensity
        triggered = self.spmtControllerObj.callWaveDumpAndTriggerDigitizer(frequency=self.highIntensAcqFreq, numberOfPulses=self.highIntensAcqPulses)

        if (triggered):
            # Then rename files for intense LED
            self.spmtControllerObj.renameWaveFilesForIntenseLED()
        else:
            self.abortProgram(executionStep="triggering digitizer and running WaveDump to acquire waves at intense LED")
            return -1

        print("----------------------------------------------------------------")
        print("-:- Low LED light -:-")
        print("----------------------------------------------------------------")
        # --------------------------------------------------------------------
        # Low LED light start...
        self.informExecution.emit("Acquiring and processing low LED light...")
        # --------------------------------------------------------------------
        # Reset all voltages of operational channels
        self.spmtControllerObj.setVoltageToAllChannels(voltage=self.lowIntensVoltageLEDs/2)

        # --------------------------------------------------------------------
        # Store voltages for single photoelectron
        storedVoltagesPh = self.spmtControllerObj.storeVoltagesForSinglePhotoelectron(voltagesArray=listOfVoltagesRead, voltageLowLED=self.lowIntensVoltageLEDs, voltageFactor=self.lowIntensVoltageFactor)

        if (not storedVoltagesPh):
            self.abortProgram(executionStep="storing voltages for single photoelectron and low LED")
            return -1

        # --------------------------------------------------------------------
        # Acquire new WaveDump files with LED configured with low intensity
        triggered = self.spmtControllerObj.callWaveDumpAndTriggerDigitizer(frequency=self.lowIntensAcqFreq, numberOfPulses=self.lowIntensAcqPulses)

        if (triggered):
            # Then rename files for low LED
            self.spmtControllerObj.renameWaveFilesForLowLED()
        else:
            self.abortProgram(executionStep="triggering digitizer and running WaveDump to acquire waves at low LED")
            return -1

        # --------------------------------------------------------------------
        # Finally, call Single Photoelectron processing
        processedSingle = self.spmtControllerObj.callSinglePhotoelectronProcess()

        if (not processedSingle):
            self.abortProgram(executionStep="processing single photoelectron from acquired data")
            return -1

        print("----------------------------------------------------------------")
        print("-:- Linearity -:-")
        print("----------------------------------------------------------------")
        # --------------------------------------------------------------------
        # Linearity...
        self.informExecution.emit("Acquiring and processing linearity...")
        # --------------------------------------------------------------------
        # Power off LED_1 (of single photoelectron) which is connected to channel 8, so, simply set "0" voltage output to that channel
        self.spmtControllerObj.setVoltageToOneChannel(channel=self.channelOfLED_1, voltage=0)

        # --------------------------------------------------------------------
        # Read voltages gain to calculate new voltages to set before linearity procedure...
        listOfNewVoltages, readVoltagesGain = self.spmtControllerObj.readVoltagesCalculatedBySinglePhotoelectron(voltagesArray=listOfVoltagesRead, voltageFactor=self.linearityVoltageFactor)

        if (not readVoltagesGain):
            self.abortProgram(executionStep="reading voltages gain calculated by single photoelectron")
            return -1

        # --------------------------------------------------------------------
        # Reset all voltages of operational channels (divide each element by 2 before to pass it)
        setNewVoltages = self.spmtControllerObj.setVoltageToAllChannelsByArray(voltagesArray=[i / 2 for i in listOfNewVoltages])

        if (not setNewVoltages):
            self.abortProgram(executionStep="setting new voltages before linearity processing")
            return -1

        # --------------------------------------------------------------------
        # Save configuration of linearity processing
        savedConfigLinearity = self.spmtControllerObj.storeLinearityConfiguration(numberOfColpi=numberOfColpi, numberOfSteps=numberOfSteps)

        if (not savedConfigLinearity):
            self.abortProgram(executionStep="saving configuration file with parameters for linearity processing")
            return -1

        # --------------------------------------------------------------------
        # Acquire new WaveDump files meanwhile alternate LED 2 and 3 voltages during desired number of steps
        startedWaveDump = self.spmtControllerObj.startWaveDumpAcquisition()
        # Call WaveDump program
        startedWaveDump = startedWaveDump and self.spmtControllerObj.callWaveDump()

        if (not startedWaveDump):
            self.abortProgram(executionStep="starting WaveDump during linearity data acquisition")
            return -1

        # --------------------------------------------------------------------
        # Repeat acquisition for desired number of steps, recalculating voltages for LEDs 2 and 3
        for step in range(numberOfSteps):
            # Recalculate voltages...
            self.voltageLED_2 = self.initialVoltageLED_2 + (step * self.incrementLED_2)
            self.voltageLED_3 = self.initialVoltageLED_3 + (step * self.incrementLED_3)

            # --------------------------------------------------------------------
            # (1) Set voltages...
            # --------------------------------------------------------------------
            # LED_2 in channel "9"
            self.spmtControllerObj.setVoltageToOneChannel(channel=self.channelOfLED_2, voltage=(self.voltageLED_2 / 2))
            # LED_3 in channel "10"
            self.spmtControllerObj.setVoltageToOneChannel(channel=self.channelOfLED_3, voltage=0)

            if (self.activeDebugging):
                print("---------")
                print("LEDs during linearity data acquisition: <A> ON and <B> OFF.")
                print("---------")

            # Call Trigger
            triggered = self.spmtControllerObj.triggerDigitizer(frequency=self.linearityAcqFreq, numberOfPulses=self.numberOfColpi)

            if (not triggered):
                self.abortProgram(executionStep="triggering digitizer and running WaveDump to acquire linearity data")
                return -1

            # --------------------------------------------------------------------
            # (2) Set voltages...
            # --------------------------------------------------------------------
            # LED_3 in channel "10"
            self.spmtControllerObj.setVoltageToOneChannel(channel=self.channelOfLED_3, voltage=(self.voltageLED_3 / 2))

            if (self.activeDebugging):
                print("---------")
                print("LEDs during linearity data acquisition: <A> ON and <B> ON.")
                print("---------")

            # Call Trigger
            triggered = self.spmtControllerObj.triggerDigitizer(frequency=self.linearityAcqFreq, numberOfPulses=self.numberOfColpi)

            if (not triggered):
                self.abortProgram(executionStep="triggering digitizer and running WaveDump to acquire linearity data")
                return -1

            # --------------------------------------------------------------------
            # (3) Set voltages...
            # --------------------------------------------------------------------
            # LED_2 in channel "9"
            self.spmtControllerObj.setVoltageToOneChannel(channel=self.channelOfLED_2, voltage=0)

            if (self.activeDebugging):
                print("---------")
                print("LEDs during linearity data acquisition: <A> OFF and <B> ON.")
                print("---------")

            # Call Trigger
            triggered = self.spmtControllerObj.triggerDigitizer(frequency=self.linearityAcqFreq, numberOfPulses=self.numberOfColpi)

            if (not triggered):
                self.abortProgram(executionStep="triggering digitizer and running WaveDump to acquire linearity data")
                return -1

        # --------------------------------------------------------------------
        # Inform WaveDump to stop acquisition and close
        stopedWaveDump = self.spmtControllerObj.stopWaveDumpAcquisition()

        if (stopedWaveDump):
            # Finally, call Linearity processing
            processedLinearity = self.spmtControllerObj.callLinearityProcess()

            if (not processedLinearity):
                self.abortProgram(executionStep="processing linearity from acquired data")
                return -1
        else:
            self.abortProgram(executionStep="stopping WaveDump during linearity data acquisition")
            return -1

        print("----------------------------------------------------------------")
        print("-:- Turn the voltages off -:-")
        print("----------------------------------------------------------------")
        # --------------------------------------------------------------------
        # Turn the voltages off...
        self.informExecution.emit("Turning off the voltages...")
        self.spmtControllerObj.setVoltageToAllChannels(voltage=0)

        print("----------------------------------------------------------------")
        print("-:- End of program -:-")
        print("----------------------------------------------------------------")
        # --------------------------------------------------------------------
        # End
        self.informExecution.emit("----------------------------------------------------------------")
        self.informExecution.emit("End of program!")
        self.spmtControllerObj.closeConnection()

        return 0


# --------------------------------------------------------------------
"""
Main()
"""
def main():
    orchestrator = Orchestrator()
    orchestrator.executeProgram()


if __name__ == "__main__": main()