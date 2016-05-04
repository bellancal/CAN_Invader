import OOBDControl
import b299mca_cancodes
#from b299mca_cancodes import *
import socket
#import select
import configparser
import argparse
import logging
import sys
import binascii
import datetime
import traceback
#import ConfigFile

# Set up the CLI parser 
parser = argparse.ArgumentParser(prog="OOBD-TCP-Server", description='A simple TCP server for controlling OOBD command sequences for automated processes', epilog='This comes with NO warranty for any use, use it at your own risk!')
parser.add_argument('-s', '--server', action="store_true", help='Start in server-mode, accepting tcp connections at the port specified in the config')
parser.add_argument('-i', '--interactive', action="store_true", help='Starting interactive mode, executing commands direct from the CLI')
parser.add_argument('-c', '--command', nargs="*",  help="Executes one single Command")
parser.add_argument('-l', '--list-commands', action="store_true", help="Lists all known commands")
parser.add_argument('--DEBUG', action="store_true", help='Enables DEBUG-Mode')
parser.add_argument('--CONFIG', nargs="*", help='sets config file')
args = parser.parse_args()
# if no command line passed default to server - work around to launch window from python GUI
if not args.server and args.command is None and not args.interactive and not args.list_commands:
    args.server = True

try:
    # start oobd class
    oobd = OOBDControl.OOBDControl(args.CONFIG)
    # start cancodes
    b299mca_cancodes.cancodes_init(args.CONFIG)
    commands = b299mca_cancodes.canFunctionSets
except:
    print(50*"*")
    print("!!!RFCOMM Connection Error!!!")
    print("---Ensure BT dongle is connected and operating.---")
    print(50*"*")
# Setup debug vom CLI
DEBUG = args.DEBUG
# Setup logging
if DEBUG:
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
else:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

logging.info("Program started with CLI options: " + str(args))

cfg = configparser.ConfigParser()
# fileOK = cfg.read(ConfigFile.config_file)
fileOK = cfg.read(args.CONFIG)
if fileOK:
    print("ini file read in tcp_server = " + str(fileOK))
    host = cfg['SERVER']['HOST']
    port = int(cfg['SERVER']['PORT'])
    backlog = int(cfg['SERVER']['BACKLOG'])
    size = int(cfg['SERVER']['BUF_SIZE'])
else:
    print("Missing Config File!!")


def decodeVIN(recv):
        # print("recv=" + recv)
        if recv == "":
            return "Error"
        if isinstance(recv, bytes):
            recv = recv.decode("ascii")

        recv = recv.replace("22f190\r62f190", "")  # strip echo from answer
        recv = recv.replace("62f190", "")  # strip echo from answer
        recv = recv.replace(".\r>", "")  # strip trailing data from answer
        recv = recv.replace("\r", "")  # strip CR's
        recv = recv[:34] # only 17 characters
        # recv = 2*'30' # testing only
        # print("recv=" + recv)
        # VIN is 17 characters
        try:
            temp = binascii.unhexlify(recv)  # generate ascii characters from the hex values
        except binascii.Error:
            # non valid ascii data sent
            print(binascii.Error)
            return "Error"
        print("recv2=" + str(temp))
        vin = temp.decode("ascii")  # encode as ASCII - done
        # logging.info("Got VIN:" + vin)
        return vin


def doCommand(command):
    global commands
    if command == "connect":
        print("tcp_server attempt connect.....")
        a=oobd.connect()
        #logging.info("Connect result is ")
        print("tcp_server connect attempt complete.....  result is =")#+ str(a))
        if a.find("dead network") > 0:
            print(">>>>>>>>>>>>>>No BT device detected on PC<<<<<<<<<<<<<")
        elif a.find("period of time") > 0:
            print(">>>>>>>>>>>>>>>CAN Invader not in range<<<<<<<<<<<<<<<")
        elif a == 'OK':
            print("Connected OK")
        else:
            print("unknown")
    elif command == "disconnect":
        oobd.disconnect()
    elif command[:12] == "configureCAN":
        logging.info("+++++Trying configure command: " + command + "...")
        # command line config = configureCAN,sss,tt:ID | sss=[125,500] tt=[hs,ms]
        print("Configure CAN...")
        CAN_bus_type = cfg['CAN']['busType']
        CAN_speed = cfg['CAN']['speed']
        CAN_ID = cfg['CAN']['defaultReqID']
        # check for command line args
        i = command.find(",")  # added by LVB
        if i > 10:  # added by LVB
            CAN_speed = command[i + 1:i + 4]
            CAN_bus_type = command[i + 5: i + 8]

        j = command.find(":")
        if j>10:
            CAN_ID = command[j + 1:]
            print("j=" + j)

        print("Bus=" + CAN_bus_type + " Speed=" + CAN_speed)
        r = oobd.configureCAN(ms_hs=CAN_bus_type, reqId=CAN_ID, speed=[cfg['CAN']['addressing'], int(CAN_speed)], filterCanID=[1,cfg['CAN']['filterStart']], filterMask=[1,cfg['CAN']['filterMask']])
        if r:
            client.send(b'ConfigOK')
        print("Config Result is " + str(r))
        # oobd.configureCAN(ms_hs="ms", reqId=cfg['CAN']['defaultReqID'], speed=["11b", 125], filterCanID=[1,cfg['CAN']['filterStart']], filterMask=[1,cfg['CAN']['filterMask']])
    elif command[:15] == "testerPresentOn":
        logging.info("+++++Trying command "+command+"...")
        i = command.find(",")  # added by LVB
        if i > 14:  # added by LVB
            rID = command[i + 1:]
        else:
            rID = None
        oobd.testerPresent(active=True, reqId=rID, interval=int(cfg['CAN']['TesterPresentIntervall']))
    elif command[:16] == "testerPresentOff":
        logging.info("+++++Trying command "+command+"...")
        i = command.find(",")  # added by LVB
        if i > 14:  # added by LVB
            rID = command[i + 1:]
        else:
            rID = None    
        oobd.testerPresent(active=False, reqId=rID, interval=int(cfg['CAN']['TesterPresentIntervall']))
    elif command[:7] == "readVIN":
        print("read VIN")
        logging.info("+++++Trying command "+command+"...")
        command = commands[command]
        if command["access"] == "03":
            oobd.sendCanData(["1003"],reqId=command["reqID"]) # AHU wants the accesslevel to be set even if 2f mode
        recv = oobd.sendCanData([command["cmd"]+command["DID"]+command["parameter"] + command["data"]], reqId=command["reqID"], checkAnswer=False)
        logging.info("Result--> " + str(recv))

        vin = decodeVIN(recv[0])
        print("vin = " + vin)
        if vin.find("Error") == -1:
            print("writing VIN to file...")
            timestamp = datetime.datetime.now().strftime('%B.%d.%Y %H:%M:%S')  # Generate current timestamp
            # mode a Opens a file for appending. The file pointer is at the end of the file if the file exists.
            # That is, the file is in the append mode. If the file does not exist, it creates a new file for writing.
            vin_logfile = open('vin.log', 'a')
            vin_logfile.write(timestamp + ": " + vin + "\n")  # Append VIN to logfile
            vin_logfile.close()
        else:
            print("VIN not valid")
            client.send(b'VIN Error')

    elif command == "readSingleVIN":
        logging.info("+++++Trying command "+command+"...")
        command = commands["readVIN"]
        if command["access"] == "03":
            oobd.sendCanData(["1003"],reqId=command["reqID"])  # AHU wants the accesslevel to be set even if 2f mode
        recv = oobd.sendCanData([command["cmd"]+command["DID"]+command["parameter"]+command["data"]], reqId=command["reqID"], checkAnswer=False)
        vin = decodeVIN(recv[0])
        
        vin_logfile = open('vin_single.log', 'w')
        vin_logfile.write(vin)  # Write VIN to single vin logfile
        vin_logfile.close()
    elif command[:3] == "raw":
        i = command.find(",")  # added by LVB
        print("delimiter =" + str(i))  # added by LVB
        if i>3:    # added by LVB
            rID = command[i+1:]  # added by LVB
            com = [command[3:i]]  # added by LVB
        else:
            rID = None
            com = [command[3:]]   # added by LVB

        oobd.sendCanData(com, reqId=rID, checkAnswer=True)  # changed by LVB
        
    elif command[:5] == "reqID":
        oobd.configureCAN(reqId=command[6:])
    else:
        logging.info("+++===Trying command "+command+"...")
        # set unreal value to check later and fill with data passed via command line
        new_data = '-1'
        if command[:10] == "setVolumeX":
                i = command.find(",")  # added by LVB
                logging.info("i = " + str(i))
                if i > 8:
                    print("Volume X=" + str(command[i+1:]))
                    new_data = command[i+1:]
                    command = command[:10]
        
        if command[:8] == "setBassX":
                i = command.find(",")  # added by LVB
                logging.info("i = " + str(i))
                if i > 6:
                    print("Bass X=" + str(command[i+1:]))
                    new_data = command[i+1:]
                    command = command[:8]
        
        if command[:8] == "setTrebX":
                i = command.find(",")  # added by LVB
                logging.info("i = " + str(i))
                if i > 6:
                    print("Treb X="+str(command[i+1:]))
                    new_data = command[i+1:]
                    command = command[:8]
        
        if command[:8] == "setFreqX":
                i = command.find(",")  # added by LVB
                logging.info("i = " + str(i))
                if i > 6:
                    print("Freq X=" + str(command[i+1:]))
                    new_data = format(int(command[i+1:]) - 875, '02x')
                    command = command[:8]

        # print("test line " + str(command)) #test line OK to remove later
        #load the data from the command defintions in the cancodes file
        ncommand = commands[command]

        # assign the data value if it was not changed above
        if new_data == '-1': # done if data was not assigned above
            print("assign data")
            new_data = ncommand["data"]
        if ncommand["access"] == "03":
            print(str(ncommand) + " access = 03")
            print([ncommand["cmd"] + ncommand["DID"] + ncommand["parameter"] + ncommand["access"] + new_data])
            a = oobd.sendCanData(["1003"], reqId=ncommand["reqID"])  # AHU wants the accesslevel to be set even if 2f mode
            b = oobd.sendCanData([ncommand["cmd"]+ncommand["DID"]+ncommand["parameter"]+new_data], reqId=ncommand["reqID"], checkAnswer=False)
            #oobd.sendCanData(["1003"], reqId=ncommand["reqID"])  # AHU wants the accesslevel to be set even if 2f mode
            #oobd.sendCanData([ncommand["cmd"] + ncommand["DID"] + ncommand["parameter"] + new_data], reqId=ncommand["reqID"], checkAnswer=False)
        elif ncommand["access"] == "01":
            print(str(ncommand) + " access = 01")
            print([ncommand["cmd"] + ncommand["DID"] + ncommand["parameter"] + ncommand["access"] + new_data])
            a = oobd.sendCanData(["1001"], reqId=ncommand["reqID"]) # AHU wants the accesslevel to be set even if 2f mode
            b = oobd.sendCanData([ncommand["cmd"] + ncommand["DID"] + ncommand["parameter"] + new_data], reqId=ncommand["reqID"], checkAnswer=False)
    
        else:
            a = oobd.sendCanData([ncommand["cmd"] + ncommand["DID"] + ncommand["parameter"] + new_data], reqId=ncommand["reqID"], checkAnswer=False)

        answer = str(a) + str(b)
        logging.info("Result--> " + answer)
        if answer.find("Error") > 0 or answer == "['']['']" or answer == "['']" :
            logging.info("-->!!!Error Sending Last Command!!!")
            client.send(b'Error')

       # print("Command result =" + answer)
# Read Data out of the config file...

# commands = b299mca_cancodes.canFunctionSets

if args.server and args.command is None and not args.interactive and not args.list_commands:
    logging.debug("Starting in server mode!")
    # open a TCP socket for incoming commands
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.bind((host, port))
    s.listen(backlog) 
    s.settimeout(2) 

    # Some helper vars...
    noOfSockTimeouts = 0

    # Mainloop, waiting for commands
    while True:
        try:
            client, address = s.accept() 
            print("Client " + str(address) + " connected!")
            data = client.recv(size) 
            if data:
                try:
                    doCommand((data.decode(errors='strict')).strip())
                except:
                    if DEBUG is True:
                        print(traceback.format_exc())
                    logging.error('Command Execution failed!')
                client.send(b'OK')
                client.close()
        except (KeyboardInterrupt, SystemExit):
            s.close()
            exit()
        except socket.timeout:
            try:
                noOfSockTimeouts += 1
                if (noOfSockTimeouts % 2) == 1:
                    print("waiting for connection on port "+cfg['SERVER']['PORT']+"   ", end="\r")
                else:
                    print("waiting for connection on port "+cfg['SERVER']['PORT']+"...", end="\r")
            except:
                if DEBUG is True:
                    print(traceback.format_exc())
                s.close()
                exit()
        except:
            if DEBUG is True:
                print(traceback.format_exc())
            s.close()
            exit()
elif not args.server and args.command is not None and not args.interactive and not args.list_commands:
    logging.debug("Starting in command mode!")
    print(str(args.command))
    for command in args.command:
        doCommand(str(command).strip())
    
elif not args.server and args.command is None and args.interactive and not args.list_commands:
    logging.debug("Starting in interactive mode!")
    while True:
        inBuf = input()
        try:
            doCommand(inBuf)
        except KeyError:
            logging.info("Command not found!")
elif not args.server and args.command is None and not args.interactive and args.list_commands:
    logging.debug("Listing commands...")
    print("Available commands:")
    for command in commands:
        print(command)
else:
    logging.warning("Error parsing command line!")
