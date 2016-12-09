#!/usr/bin/env python3.4
"""
Control all the communicattion with Linduino, sending to them the commands necessary to control DAQ and also control auxiliary softwares that control Wavedump.
"""
import serial
import subprocess
import os

from time import sleep

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
        self.errorDacFileName       = "./logs/ERROR_DAC_UNICAMP.log"        # File name of error log when DAC presents problem
        self.errorModuleFileName    = "./logs/ERROR_MODULE_UNICAMP.log"     # File name of error log when Module presents problem
        self.errorPmtFileName       = "./logs/ERROR_PMT_UNICAMP.log"        # File name of error log when PMT presents problem
        self.comunicaWaveDumpFileName = "./comunicazioneW.txt"              # File to help contacting WaveDump modified and control it
        self.darkCountGaussFileName = "./Parametri_gaussiana_dark.cfg"      # File of configuration of gaussian for dark count
        self._10PercentFileName     = "./Cerca.txt"                         # File with result of 10Percento program execution
        self.waveOriginFileName     = "./wave%d.txt"
        self.waveSinglePhotoeletronFileName = "./wave%d_ph.txt"

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


    def validateModuleMonitor(self, voltagesArray, monitorArray, vFactor=5.1, iFactor=1.2541993281, maxVMonError=0.03, maxIMonError=0.03):
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
            print("Error writing START to file of comunication to WaveDump: %s..." % self.comunicaWaveDumpFileName)
            status = False
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
            print("Error writing STOP to file of comunication to WaveDump: %s..." % self.comunicaWaveDumpFileName)
            status = False
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
            # Remove previous configuration file for dark count
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


    def renameWaveFilesForSinglePhotoelectron(self):
        for channel in range(self.getNumberOfChannels()):
            try:
                if (os.path.exists(self.waveOriginFileName % channel)):
                    os.rename(self.waveOriginFileName % channel, self.waveSinglePhotoeletronFileName % channel)
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


# ----------------------------------------------------------------
def calcNewVoltageLED(voltageLED, a, b, c, factor1, factor2):
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


def abortProgram(spmtController=None, executionStep="unknow"):
        print("----------------------------------------------------------------")
        print("Error when %s.  Aborting the program..." % (executionStep))
        print("----------------------------------------------------------------")

        # Close connection, if any
        if (spmtController):
            spmtController.closeConnection()


"""
Main()
"""
def main():
    print("----------------------------------------------------------------")
    print("-:- Start of program -:-")
    print("----------------------------------------------------------------")

    # Instantiate an object of SMPT Controller
    spmtControllerObj = SmallPhotoMultiplierTubeController()
    # Only for commissioning
    spmtControllerObj.setDebug(True)

    print("----------------------------------------------------------------")
    print("-:- Set initial voltages -:-")
    print("----------------------------------------------------------------")
    # --------------------------------------------------------------------
    # Send initial voltage
    initialVoltage = 1.75
    # Initialize all voltages of operational channels
    spmtControllerObj.setVoltageToAllChannels(voltage=initialVoltage/2)

    print("----------------------------------------------------------------")
    print("-:- Enable MUX and get current Voltages -:-")
    print("----------------------------------------------------------------")
    # --------------------------------------------------------------------
    # Enable MUX and check voltages...
    listOfVoltagesRead = spmtControllerObj.setMuxToAllChannels(enable=True)

    print("----------------------------------------------------------------")
    print("-:- Disble MUX -:-")
    print("----------------------------------------------------------------")
    # --------------------------------------------------------------------
    # Disbale MUX...
    spmtControllerObj.setMuxToOneChannel()

    print("----------------------------------------------------------------")
    print("-:- Validate current voltages -:-")
    print("----------------------------------------------------------------")
    # --------------------------------------------------------------------
    # Validate read voltages
    validVoltages = spmtControllerObj.validateDACVoltages(voltagesArray=listOfVoltagesRead, reference=initialVoltage/2, maxError=0.02)

    if (not validVoltages):
        abortProgram(spmtController=spmtControllerObj, executionStep="validating DAC voltages")
        return -1
    else:
        print("Voltages OK!")

    print("----------------------------------------------------------------")
    print("-:- Read IMon and VMon -:-")
    print("----------------------------------------------------------------")
    # --------------------------------------------------------------------
    # Read IMon and VMon...
    listOfMonitorsRead = spmtControllerObj.readMonitorsOfAllChannels()


    print("----------------------------------------------------------------")
    print("-:- Validate IMon and VMon -:-")
    print("----------------------------------------------------------------")
    # --------------------------------------------------------------------
    # Validate IMon and VMon...
    validMonitor = spmtControllerObj.validateModuleMonitor(voltagesArray=listOfVoltagesRead, monitorArray=listOfMonitorsRead, vFactor=5.1, iFactor=((2100/2.5)*(100/66975)), maxVMonError=0.7, maxIMonError=0.5)

    if (not validMonitor):
        abortProgram(spmtController=spmtControllerObj, executionStep="validating IMon (PMT) and VMon (module HV)")
        return -1
    else:
        print("IMon and VMon OK!")

    print("----------------------------------------------------------------")
    print("-:- Dark count -:-")
    print("----------------------------------------------------------------")
    # --------------------------------------------------------------------
    # Dark count...
    # triggered = spmtControllerObj.callWaveDumpAndTriggerDigitizer(frequency=100, numberOfPulses=100000)     # PRODUCTION
    triggered = spmtControllerObj.callWaveDumpAndTriggerDigitizer(frequency=100, numberOfPulses=1000)

    if (triggered):
        # Then process (Dark Count) output files of WaveDump
        spmtControllerObj.callDarkCountProcess()
    else:
        abortProgram(spmtController=spmtControllerObj, executionStep="triggering digitizer and running WaveDump")
        return -1

    print("----------------------------------------------------------------")
    print("-:- Single photoelectron -:-")
    print("----------------------------------------------------------------")
    # --------------------------------------------------------------------
    # Single photoelectron...
    # --------------------------------------------------------------------
    # Initial voltage for LED_1
    voltageLED_1 = 2.5
    # Initial values of control (auxiliary) parameters
    a = 0       # Stores the value returned by 10Percento.exe program;
    b = 0       # Stores returned value of 10Percento.exe program in previous execution;
    c = 0       # Each time the direction of increment/decrement of LED voltage is inverted, "b" is incremented,
                #   then, next steps to increment/decrement LED voltage will be more thick;

    while (True):
        # LED_1 is connected to channel 8, so, simply set voltage output to that channel
        spmtControllerObj.setVoltageToOneChannel(channel=8, voltage=(voltageLED_1/2))

        # ----------------------------------------------------------------
        # Trigger CAEN digitizer running WaveDump
        # triggered = spmtControllerObj.callWaveDumpAndTriggerDigitizer(frequency=100, numberOfPulses=5000)     # PRODUCTION
        triggered = spmtControllerObj.callWaveDumpAndTriggerDigitizer(frequency=100, numberOfPulses=1000)

        if (triggered):
            # Then process (10 Percent) output files of WaveDump
            spmtControllerObj.call10PercentProcess()
        else:
            abortProgram(spmtController=spmtControllerObj, executionStep="triggering digitizer and running WaveDump during single photoelectron measuring")
            return -1

        # ----------------------------------------------------------------
        # Logic to incread/decrease LED_1 intensity
        a = spmtControllerObj.read10PercentResultContent()

        # ---------
        if (a == 0):
            break

        # ---------
        voltageLED_1, a, b, c = calcNewVoltageLED(voltageLED_1, a, b, c, 0.2, 5)

        # ---------
        c = a

    # --------------------------------------------------------------------
    # Acquire new WaveDump files with LED configured with 10 percent
    # triggered = spmtControllerObj.callWaveDumpAndTriggerDigitizer(frequency=100, numberOfPulses=100000)     # PRODUCTION 
    triggered = spmtControllerObj.callWaveDumpAndTriggerDigitizer(frequency=100, numberOfPulses=1000)

    if (triggered):
        # Then rename files for single photoeletron
        spmtControllerObj.renameWaveFilesForSinglePhotoelectron()
    else:
        abortProgram(spmtController=spmtControllerObj, executionStep="triggering digitizer and running WaveDump to acquire waves at 10 percent")
        return -1


    print("----------------------------------------------------------------")
    print("-:- Inizio luce LED intensa -:-")
    print("----------------------------------------------------------------")

    print("----------------------------------------------------------------")
    print("-:- Linearity -:-")
    print("----------------------------------------------------------------")
    # --------------------------------------------------------------------
    # Linearity...

    print("----------------------------------------------------------------")
    print("-:- Turn the voltages off -:-")
    print("----------------------------------------------------------------")
    # --------------------------------------------------------------------
    # Turn the voltages off...
    spmtControllerObj.setVoltageToAllChannels(voltage=0)

    print("----------------------------------------------------------------")
    print("-:- End of program -:-")
    print("----------------------------------------------------------------")
    # --------------------------------------------------------------------
    # End
    spmtControllerObj.closeConnection()

    return 0


if __name__ == "__main__": main()