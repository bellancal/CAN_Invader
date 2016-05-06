# Copyright (C) 2014 Moritz Martinius <moritz@admiralackbar.de>
# 
# oobdControl.py is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# oobdControl.py is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
#


"""
.. module:: OOBDControl
   :platform: Unix, Windows
   :synopsis: Control class for the open source CANInvader developed by oobd.org

.. moduleauthor:: Moritz Martinius (moritz@admiralackbar.de)


"""

from bluetooth import *
import time
import configparser
#import sys
import traceback
#import binascii
import select
import logging
from ConfigFile import *
#import tcp_server
#import ConfigFile


# bt functions located C:\Python34\Lib\site-packages\bluetooth
# Setup config file
#cfg = configparser.ConfigParser()


def signal_handler(signum, frame):
    raise Exception("Timeout!")


class OOBDControl(object):
    """
    This is the OOBDControl class that is used for configuring the CanInvader Hardware
    and sending/receiving data over it.

    .. note::
    CanInvader Hardware can be purchased at http://caninvader.de/
    """
    # Setup config file
    cfg = configparser.ConfigParser()


    def __init__(self, config):
        self.socket = BluetoothSocket(RFCOMM)
        self.connectionStatus = False
        self.filterCanId = [1, "700"]  # using 000 will reboot device as it cannot handle full bus load
        self.filterMask = [1, "700"]
        self.currentReqId = ""
        self.ms_hs = ""
        self.speed = []
        self.config = config
        print("OODB Start...")
        # fileOK = cfg.read(CFT)
        fileOK = self.cfg.read(config)
        if fileOK:
            print("ini file read in OOBD = " + str(fileOK))
        else:
            print("Missing Config File in OODB!!")

    def __del__(self):
        if self.connectionStatus is True:
            self.disconnect()

    def connect(self):
        r=''
        """
    This procedure connects to the dongle. This is usually the first thing you want to do.
    :returns: bool 
    :raises: IOError
    """
        if self.connectionStatus is True:
            logging.info('You are already connected, aborting connection attempt...')
            return False
        else:
            for retries in range(1, int(self.cfg['MAIN']['MAX_RETRIES']) + 1):
                try:
                    logging.info('Connecting to Dongle (Attempt ' + str(retries) + ')')
                    self.socket = BluetoothSocket(RFCOMM)
                    if self.socket.connect((self.cfg['DONGLE']['MAC'], 1)):  # connect to MAC-Address in the config at port 1
                        self.socket.setblocking(1)  # See below
                        self.socket.settimeout(1)
                        # Nasty bug! Doesn't work with the MS BT stack, bug in PyBluez, see Issue 40
                        # http://code.google.com/p/pybluez/issues/detail?id=40
                    time.sleep(1)  # Dirty workaround for bug above
                    while True:
                        recvBuf = self.sendCtrlSeq(['p 0 0 0'], False)
                        time.sleep(0.5)  # Dirty workaround for bug above
                        if "OOBD" in str(recvBuf[0]):
                            self.connectionStatus = True
                          # ConfigFile.User_Connect = True

                            logging.info('Connected to OOBD-Dongle True!')
                            #break
                            return "OK"
                        else:
                            self.socket.close()
                            self.connectionStatus = False
                            time.sleep(1)
                            logging.error("Probably not an OOBD-Dongle or device not booted yet...")
                            raise IOError
                except: # IOError, :
                    time.sleep(1)
                    r = '!!!!!Connection Error:' + traceback.format_exc()
                    # logging.error(r)
                    # OS error dead network means no BT dongle detected.  Timeout means CAN  INVADER not detected
                    print("retry " + str(retries) + " completed.")
        return r

                    # continue
                #print("3 tries done")
       # if r.index("dead network") > 0:
          #  return 'No BT Dongle'
       # else:


    def sendCtrlSeq(self, seq, retry):
        """
        This function sends a control sequence to the dongle (p-commands)

        :param seq: List of strings with p-commands
        :type seq: list
        :returns: bool 
        """
        res = []

        logging.info("sendCtrlSeq = " + str(seq) + "  - retry =" + str(retry))

        for command in seq:
            try:
                res.append(self.sendRawData(data=command + "\r"))
            except:
                logging.error("Error in sendCtrlSeq: " + traceback.format_exc())
                self.socket.close()
                self.connectionStatus = False
                if retry:
                    try:  # Try reconnect
                        print("Forcing connect...")
                        self.connect() # attempts a connection if not already connected!!
                        self.configureCAN(self.ms_hs, self.currentReqId, self.speed, self.filterCanId, self.filterMask)
                        if self.sendCtrlSeq(seq) is not False:  # if exception occurs, the parent sendCtrlSeq goes to exception so no need for checking if sending attempt is retry
                            return True
                    except:  # reconnecting failed
                        logging.error("Error reconnecting")
                        print(traceback.format_exc())
                        return False
                else:
                    print("Failed sendctrl no retry")
                    return False

        print("sendCtrlSeq Result: " + str(res))
        return res

    def disconnect(self):
        """
        This procedure disconnects the dongle and resets it (all configuration done via configureCAN will be lost!)
        
        :returns: bool 
        """
        logging.info('Disconnecting from dongle...')

        self.sendCtrlSeq(["p 0 99 0 0"], retry=False)  # reboots the device, just in case...

        self.socket.close()

        self.connectionStatus = False

        return True

    def formatAnswer(self, recv):
        """
        This function formats the received data to a human readable output string
        
        :param recv: Input string directly received from the dongle.
        :type recv: str
        :returns: bool 
        """
        if isinstance(recv, list):
            outBuf = []
            for inBuf in recv:
                strippedCR = inBuf.replace(b"\r", b"")
                outBuf.append(((strippedCR).decode(encoding='UTF-8'))[0:-2].replace(" ", "").lower())
            return outBuf
        else:
            return False

    # configureCAN(parameters=[MS_HS, speed, filter_start, filter_stop])...
    def configureCAN(self, ms_hs="hs", reqId="000", speed=["11b", 500], filterCanID=[1, "700"], filterMask=[1, "700"]):
        """
        This function is a helper class for configuring common scenarios for the CAN-Bus. For advanced configuration, use sendRawData and consult the OOBD documentation (http://oobd.org/doku.php?id=doc:hw_commands)

        :param ms_hs: Which relay position to use, either HighSpeed CAN or LowSpeed CAN. Without function with dongles equipped with manual switch.
            Pass either "hs" for high-speed or "ms" for mid-speed switch position
        :type ms_hs: str
        :param reqId: Default RequestID for sending CAN frames
        :type reqId: str
        :param speed: Adressing mode and speed for sending CAN Frames
        :type speed: list
        :param filterCanID: set Filter CAN-ID (11bit CAN-ID 0x0000-0x07FF). First list parameter is the filter Number, second is the Filter ID.
        :type filterCanID: list
        :param filterMask: set Filter Bitmask (11bit CAN-ID Mask 0x0000-0x07FF, 0=don't care; 1=match)
        :type filterMask: list
        :returns:  bool 
        """
        configString = ["p 8 2 0 0"]  # initial config string CAN transceiver: Silent mode (CAN deactive)

        # safe configuration to locals
        self.filterCanID = filterCanID
        self.filterMask = filterMask
        self.currentReqId = reqId
        self.ms_hs = ms_hs
        self.speed = speed

        if ms_hs == "ms":
            configString.append("p 8 4 1 0") # MS-CAN (Relais switch - ON)
        elif ms_hs == "hs":
            configString.append("p 8 4 0 0") # HS-CAN (Relais switch - OFF)

        if speed[0] == "11b":  # 11b addressing
            if speed[1] == 125:
                configString.append("p 8 3 1 0")
            elif speed[1] == 250:
                configString.append("p 8 3 2 0")
            elif speed[1] == 500:
                configString.append("p 8 3 3 0")
            elif speed[1] == 1000:
                configString.append("p 8 3 4 0")

            configString.append("p 8 2 3 0") # CAN active mode
            configString.append("p 6 5 $" + reqId)  # set ECU Request-ID (RECVID)

            if filterCanID:
                configString.append("p 8 10 " + str(filterCanID[0]) + " $" + filterCanID[1])
            if filterMask:
                configString.append("p 8 11 " + str(filterMask[0]) + " $" + filterMask[1])
        elif speed[0] == "29b":
            if speed[1] == 125:
                configString.append("p 8 3 5 0")
            elif speed[1] == 250:
                configString.append("p 8 3 6 0")
            elif speed[1] == 500:
                configString.append("p 8 3 7 0")
            elif speed[1] == 1000:
                configString.append("p 8 3 8 0")

            configString.append("p 8 2 3 0")
            configString.append("p 6 5 $" + reqId)

            if filterCanID: # 29bit CAN-ID
                configString.append("p 8 12 " + str(filterCanID[0]) + " $" + filterCanID[1])
            if filterMask:
                configString.append("p 8 13 " + str(filterMask[0]) + " $" + filterMask[1])

        # set the timeout value for responses
        # set response timeout in 10ms units - 4 = 40ms
        configString.append("p 6 1 4 0")

        logging.info("Config String sent to dongle: " + str(configString))

        try:
             a = False
             a = self.sendCtrlSeq(configString, retry=False)
        except:
            print("Configuration FAILED!!")
            return False

        return a
        #if self.sendCtrlSeq(configString, False) is not False:
         #   return True
        #else:
        #    print("Configuration FAILED!!")
        #   return False

    def sendRawData(self, data):
        """
        This function sends raw data to the CANInvader Dongle over the connected Bluetooth socket.
        Use with care and consult the OOBD documentation (http://oobd.org/doku.php?id=doc:hw_commands)
        Now with more speed!
        
        :param data: The string you want to send to the dongle. Encoding is done for you, no need to use a bytes string!
        :type data: str
        :returns:  str 
        """
        logging.debug("RawData: " + data)
        self.socket.send(bytes(data, "utf-8").decode("unicode_escape"))

        recv_buf = b""
        ready = select.select([self.socket], [], [], 1)
        # readable, writable, exceptional = select.select(inputs, outputs, inputsforerrors, timeout)
        # waits for activity on RFCOMM - returns null after timeout
        while ready[0]:
            recv_buf += self.socket.recv(1)
            if recv_buf[-3:-1] == b".\r":
                break
            ready = select.select([self.socket], [], [], 1)

        return recv_buf

    def sendCanData(self, seq, reqId=None, checkAnswer=False):
        """
        This function allows you to send CAN-Data directly onto the bus
        
        :param seq: A list of strings of the CAN-Data you want to send. 
        :type seq: list
        :param reqId: The RequestID you want to send to. If left blank, the reqId configured in the configureCAN function is used
        :type reqId: str
        :param checkAnswer: Checks for positive CAN response (+0x40 on first sent byte) and returns False if it fails
        :type checkAnswer: bool
        :returns: list 
            List of strings with each corresponding answer by the dongle
        """
        res = []
        reqId = reqId or self.currentReqId  # Python doesn't accept variables as default parameters, use this
        logging.info('Sending CAN Commands:' + str(seq) + ' reqId:' + str(reqId))

        # workaround to set ReqId if one is omitted, else use currentReqId
        #try:
        self.sendCtrlSeq(["p 6 5 $" + reqId], retry=False)
        #except:

        currentAnswer = "Error" #assume error until cleared.
        for command in seq:
            try:
                sid_tx = int(command[0:2], 16)
                sid_rx = -1  # set to bad answer first and replace with good answer if possible
                currentAnswer = self.sendRawData(data=command + "\r").decode("ascii")
                # res.append(currentAnswer)
                currentAnswer = currentAnswer.replace(command + "\r", "")
                currentAnswer = currentAnswer.replace("\r", "")
                res.append(currentAnswer)
                if checkAnswer is True:

                    # sid_tx = int(command[0:2], 16)

                    if currentAnswer[1:6] != "Error" and currentAnswer != "":  # check for error or no response
                        print("currentAnswer =" + currentAnswer)
                        sid_rx = int(currentAnswer[0:2], 16)
                    logging.info("CAN answer match?:" + str(sid_tx + 0x40) + "      " + str(sid_rx))
                    if (sid_tx + 0x40) == sid_rx:
                        logging.info("Command " + command + " has been executed successful")
                    else:
                        logging.info("Error executing command: " + command)
                        return False

            except:

                logging.error("sid_tx=" + str(sid_tx))
                logging.error("currentAnswer=" + currentAnswer[1:6])
                logging.error("Something went wrong sending or receiving over the BT socket: " + traceback.format_exc())
                self.socket.close()
                self.connectionStatus = False
                try:  # Try reconnect
                    self.connect()
                    self.configureCAN(self.ms_hs, self.currentReqId, self.speed, self.filterCanId, self.filterMask)
                    if (self.sendCtrlSeq(seq, retry = False) is not False):  # if exception occurs, the parent sendCtrlSeq goes to exception so no
                        # need for checking if sending attempt is retry
                        return True  # changed to False - was True
                except:  # reconnecting failed
                    logging.error("Error reconnecting")
                    print(traceback.format_exc())
                    return False
                return False
        return res  # was True

    def testerPresent(self, active=True, reqId=None, interval=250):
        """
        This function enables/disables sending the tester present message in the background.
        
        :param active: Sets if the periodic tester present message should be send or not
        :type active: bool
        :param reqId: The RequestID you want to send to. If left blank, the reqId configured in the configureCAN function is used
        :type reqId: str 
        :param interval: Time in ms between each tester present message
        :type interval: int
        :returns: list 
            List of strings with each corresponding answer by the dongle
        """
        reqId = reqId or self.currentReqId  # Python doesn't accept variables as default parameters, use this
        # workaround to set ReqId if one is omitted, else use currentReqId

        if active is True:
            self.sendCtrlSeq(["p 6 8 " + str(interval) + " 0", "p 6 6 $" + reqId + " 0"] , False)
            logging.info("Tester Present On")
        else:
            self.sendCtrlSeq(["p 6 7 $" + reqId + " 0"], False)
            logging.info("Tester Present Off")
        return True
