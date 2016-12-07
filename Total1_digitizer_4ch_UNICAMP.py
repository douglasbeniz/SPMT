#!/usr/bin/env python3.4
"""
Control all the communicattion with Linduino, sending to them the commands necessary to control DAQ and also control auxiliary softwares that control Wavedump.
"""
import serial

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
        self.errorDacFileName       = "ERROR_DAC_UNICAMP.log"       # File name of error log when DAC presents problem
        self.errorModuleFileName    = "ERROR_MODULE_UNICAMP.log"    # File name of error log when Module presents problem
        self.errorPmtFileName       = "ERROR_PMT_UNICAMP.log"       # File name of error log when PMT presents problem

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
        #         -> Select DAC (channel) to operate on (1-15, or 16 for All):
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


    def closeConnection(self):
        if (self.linduinoObj):
            self.linduinoObj.closeConnection()


    def __del__(self):
        self.closeConnection()


def abortProgram(spmtController=None, executionStep="unknow"):
        print("----------------------------------------------------------------")
        print("Error when validating %s.  Aborting the program..." % (executionStep))
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
    #spmtControllerObj.setDebug(True)

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
    validVoltages = spmtControllerObj.validateDACVoltages(voltagesArray=listOfVoltagesRead, reference=initialVoltage/2, maxError=0.05)

    if (not validVoltages):
        abortProgram(spmtController=spmtControllerObj, executionStep="DAC voltages")
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
        abortProgram(spmtController=spmtControllerObj, executionStep="IMon (PMT) and VMon (module HV)")
        return -1
    else:
        print("IMon and VMon OK!")

    print("----------------------------------------------------------------")
    print("-:- Dark count -:-")
    print("----------------------------------------------------------------")
    # --------------------------------------------------------------------
    # Dark count...

    print("----------------------------------------------------------------")
    print("-:- Single photoelectron -:-")
    print("----------------------------------------------------------------")
    # --------------------------------------------------------------------
    # Single photoelectron...

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
