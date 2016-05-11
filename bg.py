from tkinter import *
import tkinter.messagebox
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as font

import subprocess
from subprocess import Popen, CREATE_NEW_CONSOLE, PIPE
import os
import ConfigFile
import configparser
"""
Purpose: Main file that creates the gui using TK widgets for the CAN INVADER control.
This program will launch the BT server and initiate message using server.  This program will also monitor for server status
and CAN responses for the diagnostic requests and present these to user.

Author: Louis V Bellanca / LBELLAN1@FORD.COM
Date: April 2016 first release


"""

#TODO:auto  detect presence of amp - need to account different for volume default
#TODO:determine supplier of AHU from CAN bus.
#TODO: get input from buld sheet to decode configuration



# Define global variables here
cfg = configparser.ConfigParser()
engineering_mode = False
command_error = False
# set defaults for the size
default_sizex = "662"
default_sizey = "478"
fileOK = ""
MasterVol1 = 1
MasterVol2 = 16


def ConfigSelect(selection=None):
    print("Configuration selected = " + str(selection))
    if selection is not None:
        LoadConfig(ConfigFile.config_list2[selection]["filename"])


def LoadConfig(filetoload):
    # sub to check the config file and load data
    global sizex, sizey, fileOK, config_file
    # refer to the file to see if a config is defined
    fileOK = cfg.read(filetoload)

    if fileOK:
        print("ini file read in bg = " + str(fileOK))
        loaded_config.set("Config file = " + filetoload)

        # ConfigFile.CFT = filetoload
        print("Attempting to load config = " + filetoload)
        config_file = filetoload
        # CheckTP()
        CheckAMP()
        CheckAHU()
        CheckSpeaker()
        CheckVIN()
        CheckCAN(bus_type=cfg['CAN']['busType'].lower(), speed=cfg['CAN']['speed'].lower())
        # if the config file does not have the section 'SIZE', then add it to the config-file
        if not cfg.has_section('SIZE'):
            cfg.add_section('SIZE')
            # set default size
            sizex = default_sizex
            sizey = default_sizey
            print("cfg section SIZE not found -  to be added!!")
        # else just return the the value of globle->settings
        else:
            sizex = cfg['SIZE']['X']
            sizey = cfg['SIZE']['Y']
            print ("Size x =" + sizex + " Size y =" + sizey)

        # change the window to the defined size
        root.geometry("%sx%s" % (sizex, sizey))



    else:
        print("Missing Config File!!" + str(fileOK))
        tkinter.messagebox.showinfo("Config File Error", "The specified configuration file could not be found:" + filetoload )
        loaded_config.set("Config file not found!")


def CheckCAN(bus_type=None, speed=None):
    # set gui to match default setting
        print("bus=" + bus_type + " speed=" + speed)
        if bus_type == 'hs' and speed == '500':
            sp_500_HS.set(True)
            CAN_setup0()
        elif bus_type == 'hs' and speed == '125':
            sp_125_HS.set(True)
            CAN_setup1()
        elif bus_type == 'ms' and speed == '125':
            sp_125_MS.set(True)
            CAN_setup3()
        elif bus_type == 'ms' and speed == '500':
            sp_500_MS.set(True)
            CAN_setup2()
        else:
            print("Invalid CAN settings in ini file!")



def CheckSpeaker():
    # checks for speaker type in the ini file and sets program accordingly
    # Enter in config file as:
    # [SPEAKER]
    # type = Panasonic | Clarion | Visteon
    if cfg.has_section('SPEAKER'):
        sptype = cfg['SPEAKER']['TYPE']
        sptype = sptype.lower()
        if sptype == '1':
            Speaker1.set(True)
            Sp1_change()
            print("Speaker type 1")
        elif sptype == '2':
            Speaker2.set(True)
            Sp2_change()
            print("Speaker type 2")
        elif sptype == '3':
            Speaker3.set(True)
            print("Speaker type 3")
            Sp3_change()
        else:
            print("Invalid Speaker type defined - check config")
    else:
        print("No Speaker type found")


def CheckAMP():
    """
    checks for AMP in the ini file and sets program accordingly - also determines the default volume setting
    Enter in config file as:
    [AMP]
    present = 1 | 0
    """
    global default_volume
    if cfg.has_section('AMP'):
        amptype = cfg['AMP']['PRESENT']
        amptype = amptype.lower()
        if amptype == '1':
            Amp_Present.set(True)
            print("AMP is present")
            default_volume =  cfg['AMP']['VOLUME']

        elif amptype == '0':
            Amp_Present.set(False)
            print("No AMP present")
            default_volume =  cfg['DUT']['VOLUME_FRONT']
        else:
            print("Invalid AMP type defined - check config")


    else:
        print("No AMP type found")
        default_volume =  cfg['DUT']['VOLUME_FRONT']

    loaded_volume.set('Default Volume Setting = ' + default_volume)


def AMP_autocheck():
    global default_volume
    print("Auto check for AMP")
    # do auto check for AMP
    Amp_Present.set(True) # sorce to send messsage to AMP
    if set_vol_default(0):
        print("AMP FOUND in AutoCHECK!!")
        default_volume =  cfg['AMP']['VOLUME']
    else:
        print("NO AMP FOUND in AutoCHECK!!")
        Amp_Present.set(False)
        default_volume =  cfg['DUT']['VOLUME_FRONT']

    loaded_volume.set('Default Volume Setting = ' + default_volume)


def CheckAHU():
    """
    checks for AHU type in the ini file and sets program accordingly
    Enter in config file as:
    [AHU]
    type = Panasonic | Clarion | Visteon
    """
    if cfg.has_section('AHU'):
        ahutype = cfg['AHU']['TYPE']
        ahutype = ahutype.lower()
        if ahutype == 'panasonic':
            AHU_Pana.set(True)
            AHU_changeP()
        elif ahutype == 'clarion':
            AHU_Clar.set(True)
            AHU_changeC()
        elif ahutype == 'visteon':
            AHU_Vist.set(True)
            AHU_changeV()
        else:
            print("Invalid AHU type defined - check config")
    else:
        print("No AHU type found")


def CheckTP():
    """
    checks for additional tester present ID and sends the TP On command
    Enter in config file as:
    [TESTERPRESENT]
    idlist = 7DF, 777, 711
    """

    if cfg.has_section('TESTERPRESENT'):
        canid = cfg['TESTERPRESENT']['IDLIST'].split(',')

        for id in canid:
            id = id.replace(" ", "") # remove whitespacec if present
            id = id.upper()
            print ("Enable TP for :" + id)
            testerPon(forceid=id)
    else:
        print("No additional TP")

def CheckVIN():
    """"
    checks for presence of the VIN ECU to query
    Enter in config file as:
    [VIN]
    ecu = bcm sync, ahu, ipc, bcm, abs - only list 1!!!
    """
    global VIN_ecu, vin_y, vin_x
    if cfg.has_section('VIN'):
        VIN_ecu = cfg['VIN']['ECU'].upper()
        print("VIN ecu = " + VIN_ecu)
        # hide all and show the ones  used
        HideVINbuttons()
        if VIN_ecu == "SYNC":
            print("Show VIN-SYNC")
            app.getVINsync_b.pack()
            app.getVINsync_b.place(rely=vin_y, relx=.40)
        elif VIN_ecu == "AHU":
            print("Show VIN-AHU")
            app.getVINahu_b.pack()
            app.getVINahu_b.place(rely=vin_y, relx=vin_x)
        elif VIN_ecu == "ABS":
            print("Show VIN-ABS")
            app.getVINabs_b.pack()
            app.getVINabs_b.place(rely=vin_y, relx=0)
        elif VIN_ecu == "BCM":
            print("Show VIN-BCM")
            app.getVINbcm_b.pack()
            app.getVINbcm_b.place(rely=vin_y, relx=vin_x * 2)
        elif VIN_ecu == "IPC":
            print("Show VIN-IPC")
            app.getVINipc_b.pack()
            app.getVINipc_b.place(rely=vin_y, relx=vin_x * 3)
        elif VIN_ecu == "RCM":
            print("Show VIN-RCM")
            app.getVINrcm_b.pack()
            app.getVINrcm_b.place(rely=vin_y, relx=vin_x * 4)

    else:
        print("No VIN ecu in config")

def HideVINbuttons():
    app.getVINahu_b.place_forget()
    app.getVINabs_b.place_forget()
    app.getVINsync_b.place_forget()
    app.getVINbcm_b.place_forget()
    app.getVINipc_b.place_forget()
    app.getVINrcm_b.place_forget()

def Hide(action):
    print("hiding =" + str(action))
    if action:
        app.startserver_b.place_forget()
        app.connect_b.place_forget()
        # app.setBass_b.place_forget()
        # app.setTreb_b.place_forget()
        # bass_in.place_forget()
        # treb_in.place_forget()
        app.radioOn_b.place_forget()
        app.Testerp_b.place_forget()
        app.TesterpOff_b.place_forget()
        app.Test_b.place_forget()
        tpid.place_forget()
        tpid_off.place_forget()
        HideVINbuttons()


    else:
        app.onepress_b.place_forget()
        app.startserver_b.pack(in_=app.frame)
        app.startserver_b.place(rely=.12, relx=.2)
        app.onepress_b.pack(in_=app.frame)
        app.onepress_b.place(rely=.12, relx=0)
        app.connect_b.pack(in_=app.frame)
        app.connect_b.place(rely=.12, relx=.3)
        # app.setBass_b.pack(in_=app.frame)
        # app.setBass_b.place(rely=.2, relx=0)
        # app.setTreb_b.pack(in_=app.frame)
        # app.setTreb_b.place(rely=.2, relx=.34)
        # bass_in.pack(in_=app.frame)
        # bass_in.place(rely=.21, relx=.18)
        # treb_in.pack(in_=app.frame)
        # treb_in.place(rely=.21, relx=.52)
        app.radioOn_b.pack(in_=app.frame)
        app.radioOn_b.place(rely=.12, relx=.4)
        app.Testerp_b.pack(in_=app.frame)
        app.Testerp_b.place(rely=.75, relx=.86)
        app.TesterpOff_b.pack(in_=app.frame)
        app.TesterpOff_b.place(rely=.84, relx=.86)
        app.Test_b.pack(in_=app.frame)
        app.Test_b.place(rely=.9, relx=0)
        tpid.pack(in_=app.frame)
        tpid.place(rely=.76, relx=.82)
        tpid_off.pack(in_=app.frame)
        tpid_off.place(rely=.85, relx=.82)

        app.getVINahu_b.pack()
        app.getVINahu_b.place(rely=vin_y, relx=vin_x)
        app.getVINabs_b.pack()
        app.getVINabs_b.place(rely=vin_y, relx=0)
        app.getVINsync_b.pack()
        app.getVINsync_b.place(rely=vin_y, relx=vin_x * 5)
        app.getVINbcm_b.pack()
        app.getVINbcm_b.place(rely=vin_y, relx=vin_x * 2)
        app.getVINipc_b.pack()
        app.getVINipc_b.place(rely=vin_y, relx=vin_x * 3)
        app.getVINrcm_b.pack()
        app.getVINrcm_b.place(rely=vin_y, relx=vin_x * 4)


def quitme():
    # write the window size to the ini file for next startup
    global fileOK, servercmd, config_file
    if fileOK:
        cfg.set('SIZE', 'X', str(root.winfo_width()))
        cfg.set('SIZE', 'Y', str(root.winfo_height()))
        print("Saving Configuration data...")
        cfg.write(open(config_file, "w"))
    disconnect()
    try:
        servercmd.kill()
    except:
        pass
    sys.exit()


def left_mouse(event):
    print("Left Mouse @ {},{}".format(event.x, event.y))


def right_mouse(event):
    print("Right Mouse @ {},{}".format(event.x, event.y))


def a_key(event):
    global engineering_mode
    global MasterVol1, MasterVol2
    print("{},{}".format(event.x, event.y), event.char)
    if event.char == 'E':
        engineering_mode = not engineering_mode
        Hide(not engineering_mode)
        print("toggle engineering mode = " + str(engineering_mode))
    elif event.char == 'T':
        CheckVIN()
    elif event.char == '+':
        # create a popup menu  self.setVol1_b = Button(master, text="Vol=1", command=set_vol1, fg="white", bg="green")
        if MasterVol1 < 30:
            MasterVol1 += 1
            app.setVol1_b.configure(text="Vol=" + str(MasterVol1))
    elif event.char == '-':
        # create a popup menu  self.setVol1_b = Button(master, text="Vol=1", command=set_vol1, fg="white", bg="green")
        if MasterVol1 > 0 :
            MasterVol1 -= 1
            app.setVol1_b.configure(text="Vol=" + str(MasterVol1))

    elif event.char == '>':
        # create a popup menu  self.setVol1_b = Button(master, text="Vol=1", command=set_vol1, fg="white", bg="green")
        if MasterVol2 < 30:
            MasterVol2 += 1
            app.setVol16_b.configure(text="Vol=" + str(MasterVol2))
    elif event.char == '<':
        # create a popup menu  self.setVol1_b = Button(master, text="Vol=1", command=set_vol1, fg="white", bg="green")
        if MasterVol2 > 0 :
            MasterVol2 -= 1
            app.setVol16_b.configure(text="Vol=" + str(MasterVol2))
        #     popupw = Menu(root, tearoff=0)
    #     popupw.add_command(label="Display the label")
    #     popupw.add_command(input("hi"))
    #     # display the popup menu
    #     try:
    #         popupw.tk_popup(event.x_root, event.y_root, 0)
    #     finally:
    #         # make sure to release the grab (Tk 8.0a1 only)
    #         popupw.grab_release()


def about():
    tkinter.messagebox.showinfo("CAN Invader BT Controller", "Ver 1.3 - April 18, 2016 \r\n Ford Motor Company \r\n Contact:LbeLLan1@Ford.com\r\n")
    print("width =" + str(root.winfo_width()))
    print("height =" + str(root.winfo_height()))
    # print (root.winfo_geometry())


def show_instructions():
    # show pdf instruction guide
    subprocess.Popen("instructions.pdf",shell=True)


def start_server():
    global command_error
    command_error = False

    print("starting server")
    global servercmd
    servercmd = subprocess.Popen([sys.executable, "tcp_server.py", "--CONFIG", config_file], creationflags=CREATE_NEW_CONSOLE)


def onepress():
    global command_error, default_volume
    print("onepress started")
    command_error = False
    start_server()
    # if connect not successful then do not perform other commands!
    a = connect()
    if a:
        AMP_autocheck() # another check to make sure of AMP presence
        radio_on()
        set_bass()
        set_treble()
        set_freq()
        set_vol_default(default_volume)


def testerPon(forceid=None):
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    command_error = False
    print("tester present on")
    id1 = tpid.get()
    if id1 != "":
        id1 = "," + id1
    if forceid is not None: # forceid takes precedence
        id1 = "," + str(forceid)
    p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'testerPresentOn' + id1], creationflags=CREATE_NEW_CONSOLE)


def testerPoff():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    command_error = False
    print("tester present off")
    id1 = tpid_off.get()
    if id1 != "":
        id1 = "," + id1
    p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'testerPresentOff' + id1], creationflags=CREATE_NEW_CONSOLE)


def connect():
    global command_error
    command_error = False
    print("BT connect")
    # filepath='"C:\Users\lbellan1\PycharmProjects\gui\start.bat"' C:/Users/lbellan1/PycharmProjects/gui/start.bat
    os.system("start /wait cmd /c bt_connect_only.bat")
    if sp_125_HS.get():
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'configureCAN,125,hs'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        print("Set CAN 125 HS")
    elif sp_125_MS.get():
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'configureCAN,125,ms'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        print("Set CAN 125 MS")
    elif sp_500_MS.get():
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'configureCAN,500,ms'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        print("Set CAN 500 MS")
    elif sp_500_HS.get():
        print("Set CAN 500 HS")
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'configureCAN,500,hs'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    else:
        print("Set CAN from ini")
        # no configuration chosen so use default in ini file
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'configureCAN'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        # CheckCAN(bus_type = cfg['CAN']['busType'].lower(), speed = cfg['CAN']['speed'].lower())

    stdout, stderr = p.communicate()
    print(stdout + stderr)
    if stdout.find(b'ConfigOK') > 0:
        global User_Connect
        User_Connect = True
        os.system("start /wait cmd /c TP_on.bat")
        CheckTP()  # keep this here
        print("Connected OK!")
        # CheckAHU()
        # CheckSpeaker()
        # CheckVIN()
        return True

    else:
        User_Connect = False
        print("Failed to connect via BT!")
        tkinter.messagebox.showinfo("Connection Error", "No BT connection made! Please check setup. Make sure server is running and BT dongle is attached to PC. Check that CAN Invader is in range and attached to vehicle." )
        return False


def radio_on():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    print("Radio On")
    # os.system("start /wait cmd /c radio_on_AHU.bat")
    p = Popen([sys.executable, "pynetcat.py",'localhost','50000','radioOnahu'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    print(stdout + stderr)
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def set_bass():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    # os.system("start /wait cmd /c setBassX.bat")
    b = bass_in.get()
    if b == "":
        b = '0E'  # max
    else:
        b = format(int(b) + 7,'02X')

    if Amp_Present.get():
        print("AMP Set BASS =" + b)
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'AMPsetBassX,' + b], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    else:
        print("Set Bass=" + b)
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'setBassX,' + b], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)

    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def set_treble():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    print("Set Treble")
    # os.system("start /wait cmd /c setTrebX.bat")
    t = treb_in.get()
    if t == "":
        t = '07'  # nominal
    else:
        t = format(int(t) + 7,'02X')


    if Amp_Present.get():
        print("AMP Set Treble =" + t)
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'AMPsetTrebX,' + t], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    else:
        print("Set Treble=" + t)
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'setTrebX,' + t], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)

    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def set_freq():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    f = fin.get()

    if f != "":
        print("Set Frequency " + f)
        p=Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'setFreqX,' + f], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    else:
        print("Set Frequency to default")
        p=Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'setFreq'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    # os.system("start /wait cmd /c setFreqX879.bat")
    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def set_vol1():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error

    v = format(MasterVol1, '02x')

    if Amp_Present.get():
        print("AMP Set Vol " + str(MasterVol1))
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'AMPsetVolumeX,' + v], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    else:
        print("Set Vol " + str(MasterVol1))
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'setVolumeX,' + v], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)

    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def set_vol5():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    if Amp_Present.get():
        print("AMP Set Vol 5")
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'AMPsetVolumeX,05'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    else:
        print("Set Vol 5")
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'setVolumeX,05'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)

    # os.system("start /wait cmd /c setVolumeX5.bat")
    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def set_vol19():
    """
    use hex vale for the function of the volume setting!!!
    """

    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error

    if Amp_Present.get():
        print("AMP Set Vol 13")
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'AMPsetVolumeX,13'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    else:
        print("Set Vol 13")
        # os.system("start /wait cmd /c setVolumeX13.bat")
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'setVolumeX,13'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)

    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False

def set_vol16():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    v = format(MasterVol2, '02x')

    if Amp_Present.get():
        print("AMP Set Vol 5" + str(MasterVol2))
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'AMPsetVolumeX,' + v], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    else:
        print("Set Vol " + str(MasterVol2))
        v = format(MasterVol2, '02x')
        # print("Set Vol 16")
        # os.system("start /wait cmd /c setVolumeX13.bat")
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'setVolumeX,' + v], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)

    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def set_vol22():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error

    if Amp_Present.get():
        print("AMP Set Vol 16")
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'AMPsetVolumeX,16'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    else:
        print("Set Vol 16")
        # os.system("start /wait cmd /c setVolumeX13.bat")
        p=Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'setVolumeX,16'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)

    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
        return False
    else:
        command_error = False
        return True


def set_volX():
    """
    Take input form gui and send in volume - needs to be sent in HEX format!!
    """
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error

    v = v_scale.get()
    if v != "":
        v = format(int(v), '02x')
        if Amp_Present.get():
            print("AMP Set Vol X =" + v)
            p = Popen([sys.executable, "pynetcat.py",'localhost','50000','AMPsetVolumeX,' + v], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        else:
            print("Set Vol X =" + v)
            p = Popen([sys.executable, "pynetcat.py",'localhost','50000','setVolumeX,' + v], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    else:  # no data entered so assume default defined in setVolumeX command that is 0
        if Amp_Present.get():
            print("AMP Set Vol X =" + v)
            p = Popen([sys.executable, "pynetcat.py",'localhost','50000','AMPsetVolumeX'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        else:
            print("Set Vol X =" + v)
            p = Popen([sys.executable, "pynetcat.py",'localhost','50000','setVolumeX'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)

    # check responses
    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def set_vol_default(v):
    global command_error

    # convert to hex for command as ini file is NOT in hex format!!
    v = format(int(v), '02x')
    if v != "":
        if Amp_Present.get():
            print("AMP Set Vol Default =" + v)
            p = Popen([sys.executable, "pynetcat.py",'localhost','50000','AMPsetVolumeX,' + v], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        else:
            print("Set Vol Default =" + v)
            p = Popen([sys.executable, "pynetcat.py",'localhost','50000','setVolumeX,' + v], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)

        stdout, stderr = p.communicate()
        if stdout.find(b'Error') > 0:
            print("Error sending last command!")
            command_error = True
            return False
        else:
            command_error = False
            return True


    else:
        print("Default volume missing")
        command_error = True
        return False



def get_VIN_AHU():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    command_error = False
    print("Get VIN ahu")
    # os.system("start /wait cmd /c log_VIN_AHU.bat")
    p = Popen([sys.executable, "pynetcat.py",'localhost','50000','readVIN'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def get_VIN_ABS():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    command_error = False
    print("Get VIN abs")
    # os.system("start /wait cmd /c log_VIN_ABS.bat")
    p = Popen([sys.executable, "pynetcat.py",'localhost','50000','readVINabs'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def get_VIN_SYNC():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    command_error = False
    print("Get VIN sync")
    p = Popen([sys.executable, "pynetcat.py",'localhost','50000','readVINsync'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    # os.system("start /wait cmd /c log_VIN_SYNC.bat")
    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def get_VIN_BCM():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    command_error = False
    print("Get VIN bcm")
    p = Popen([sys.executable, "pynetcat.py",'localhost','50000','readVINbcm'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False

# TODO-test PCM get VIN and add button
def get_VIN_PCM():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    command_error = False
    print("Get VIN pcm")
    p = Popen([sys.executable, "pynetcat.py",'localhost','50000','readVINpcm'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def get_VIN_RCM():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    command_error = False
    print("Get VIN rcm")
    p = Popen([sys.executable, "pynetcat.py",'localhost','50000','readVINrcm'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)

    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def get_VIN_IPC():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    command_error = False
    print("Get VIN ipc")
    p = Popen([sys.executable, "pynetcat.py",'localhost','50000','readVINipc'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    # os.system("start /wait cmd /c log_VIN_SYNC.bat")
    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def disconnect():
    global User_Connect
    global command_error, servercmd
    print("BT Disconnect")
    os.system("start /wait cmd /c bt_disconnect.bat")
    global User_Connect
    User_Connect = False
    command_error = False

    try:
        servercmd.kill()
    except:
        pass


def speaker_LF():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    # take into account the speaker config, AHU type, and AMP presence
    print("Speaker LF")

    # Check for AMP first
    if  Amp_Present.get():
         p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'AMPspeakerEnableLFtwt4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    # then check by AHU and speaker type
    elif AHU_Clar.get():
            if Speaker1.get(): # no tweeters
                print("AHU=Clar, Speaker=1")
                p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableLF4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
            else: # with tweeters
                p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableLFtwt4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    elif AHU_Pana.get():
            print("Panasonic")
            # os.system("start /wait cmd /c speakerEnableLFtwt_Clarion.bat")
            p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableLFtwt4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    elif AHU_Vist.get():
            # print("Visteon")
            if Speaker1.get():
                print("AHU=Visteon, Speaker=1")
                p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableLF'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
            else:
                p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableLFtwt'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)

    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def speaker_RF():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    print("Speaker RF")
    if AHU_Clar.get():
        if Speaker1.get():
            print("AHU=Clar, Speaker=1")
            p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableRF4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        else:
            p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableRFtwt4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    elif AHU_Pana.get():
        # os.system("start /wait cmd /c speakerEnableRFtwt_Panasonic.bat")
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableRFtwt4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    elif AHU_Vist.get():
        if Speaker1.get():
            print("AHU=Visteon, Speaker=1")
            p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableRF'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        else:
            p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableRFtwt'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)

    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def speaker_LR():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    print("Speaker LR")
    if AHU_Clar.get():
        if Speaker1.get():
            p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableLR4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        else:
            p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableLR4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    elif AHU_Pana.get():
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableLR4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        # os.system("start /wait cmd /c speakerEnableLR_Panasonic.bat")
    elif AHU_Vist.get():
        if Speaker1.get():
            p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableLR'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        else:
            p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableLR'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)

    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def speaker_RR():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    print("Speaker RR")
    if AHU_Clar.get():
        if Speaker1.get():
            p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableRR4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        else:
            p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableRR4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
    elif AHU_Pana.get():
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableRR4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        # os.system("start /wait cmd /c speakerEnableRR_Panasonic.bat")
    elif AHU_Vist.get():
        if Speaker1.get():
            p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableRR'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        else:
            p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableRR'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)

    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def speaker_All():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    global command_error
    print("Speaker All")
    if AHU_Clar.get():
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableAllOn4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        # os.system("start /wait cmd /c speakerEnableAllOn_Clarion.bat")
    elif AHU_Pana.get():
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableAllOn4'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        # os.system("start /wait cmd /c speakerEnableAllOn_Panasonic.bat")
    elif AHU_Vist.get():
        p = Popen([sys.executable, "pynetcat.py", 'localhost', '50000', 'speakerEnableAllOn'], creationflags=CREATE_NEW_CONSOLE, stdout=PIPE, stderr=PIPE)
        # os.system("start /wait cmd /c speakerEnableAllOn_Visteon.bat")

    stdout, stderr = p.communicate()
    if stdout.find(b'Error') > 0:
        print("Error sending last command!")
        command_error = True
    else:
        command_error = False


def speaker_Center():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    print("Speaker Center")
    os.system("start /wait cmd /c speakerEnableCntr_Clarion.bat")


def speaker_Sub():
    if not User_Connect:
        tkinter.messagebox.showinfo("No Connection", "Please connect to a CAN device")
        return
    print("Speaker Sub")
    os.system("start /wait cmd /c speakerEnableSub_Clarion.bat")


def CAN_setup0():
    if sp_500_HS.get:
        sp_125_HS.set(False)
        sp_125_MS.set(False)
        sp_500_MS.set(False)
        sp_500_HS.set(True)
        # print("sp_500=" + str(sp_500_HS.get()))
        print("CAN setup 0")


def CAN_setup1():
    if sp_125_HS.get:
        sp_125_HS.set(True)
        sp_125_MS.set(False)
        sp_500_MS.set(False)
        sp_500_HS.set(False)
        print("CAN setup 1")


def CAN_setup2():
    if sp_500_MS.get:
        sp_125_HS.set(False)
        sp_125_MS.set(False)
        sp_500_MS.set(True)
        sp_500_HS.set(False)
        print("CAN setup 2")


def CAN_setup3():
    if sp_125_MS.get:
        sp_125_HS.set(False)
        sp_125_MS.set(True)
        sp_500_MS.set(False)
        sp_500_HS.set(False)
        print("CAN setup 3")


def AHU_changeP():
    print("AHU Change")
    if AHU_Pana.get():
        print("Panasonic")
        AHU_Pana.set(True)
        AHU_Clar.set(False)
        AHU_Vist.set(False)


def AHU_changeC():
    print("AHU Change")
    if AHU_Clar.get():
        print("Clarion")
        AHU_Pana.set(False)
        AHU_Clar.set(True)
        AHU_Vist.set(False)


def AHU_changeV():
    print("AHU Change")
    if AHU_Vist.get():
        print("Visteon")
        AHU_Pana.set(False)
        AHU_Clar.set(False)
        AHU_Vist.set(True)


def Sp1_change():
    if Speaker1.get():
        Speaker2.set(False)
        Speaker1.set(True)
        Speaker3.set(False)


def Sp2_change():
    if Speaker2.get():
        Speaker1.set(False)
        Speaker2.set(True)
        Speaker3.set(False)


def Sp3_change():
    if Speaker3.get():
        Speaker1.set(False)
        Speaker2.set(False)
        Speaker3.set(True)


class App:

    def __init__(self, master):
        # reference global variables for button position  - makes organizing easier
        global speaker_y, speaker_x, volume_y, vin_y

        self.frame = Frame(master, relief=SUNKEN)
        # master.geometry("320x400")
        master.geometry("%sx%s" % (default_sizex, default_sizey))
        master.title("CAN Invader Script Controller")
        master.bind("<Button-1>", left_mouse)
        master.bind("<Button-3>", right_mouse)
        master.bind("<Key>", a_key)
        self.frame.pack()

        #  info_l1 = Label(master, text="Config... ")# + ConfigFile.config_file)
        #  info_l1.pack(side=TOP)

        # info_l2 = Label(master, text="Connection Status = NOT CONNECTED")
        # info_l2.pack(side=TOP)

        # self.about_b = Button(master, text="??", command=about, bg="black", fg="white")
        # self.about_b.pack()
        # self.about_b.place(rely=0, relx=0)

        # self.quit_b = Button(master, text="Quit", command=sys.exit, bg="red", fg="white")
        # self.hello_b.bind("<Enter>",jump)
        # self.quit_b.pack(side=BOTTOM)

        self.disconnect_b = Button(master, text="Disconnect", command=disconnect, fg="red", bg="white", height=1, width=10, font=font1)
        self.disconnect_b.pack(side=BOTTOM)
        disconnect_b_ttp = CreateToolTip(self.disconnect_b, "Disconnects BT and stops server - use if changing config")

        self.startserver_b = Button(master, text="Start Serv", command=start_server, fg="white", bg="blue")
        self.startserver_b.pack(in_=self.frame)
        self.startserver_b.place(rely=.12, relx=0)
        startserver_b_ttp = CreateToolTip(self.startserver_b, "Press First - This needs to be running for other commands to work!")

        self.connect_b = Button(master, text="Connect", command=connect, fg="blue", bg="white")
        self.connect_b.pack()
        self.connect_b.place(rely=.12, relx=.3)
        Connect_b_ttp = CreateToolTip(self.connect_b, "Connects BT, initializes CAN and starts default TP message.")

        self.radioOn_b = Button(master, text="Radio On", command=radio_on, fg="white", bg="purple")
        self.radioOn_b.pack()
        self.radioOn_b.place(rely=.12, relx=.4)

        self.setBass_b = Button(master, text="Set Bass", command=set_bass, fg="blue", bg="yellow")
        self.setBass_b.pack()
        self.setBass_b.place(rely=.2, relx=.2)
        setBass_b_ttp = CreateToolTip(self.setBass_b, "Set Bass. Enter value on right or leave blank for default.")

        self.setTreb_b = Button(master, text="Set Treb", command=set_treble, fg="blue", bg="yellow")
        self.setTreb_b.pack()
        self.setTreb_b.place(rely=.2, relx=.34)
        setTreb_b_ttp = CreateToolTip(self.setTreb_b, "Set Treble. Enter value on right or leave blank for default.")

        self.getVINahu_b = Button(master, text="VIN AHU", command=get_VIN_AHU, fg="white", bg="brown", height=2, width=7, font=font1)
        self.getVINahu_b.pack()
        self.getVINahu_b.place(rely=vin_y, relx=vin_x)
        getVINahu_b_ttp = CreateToolTip(self.getVINahu_b, "Read VIN from AHU in F190.")

        self.getVINabs_b = Button(master, text="VIN ABS", command=get_VIN_ABS, fg="white", bg="brown", height=2, width=7, font=font1)
        self.getVINabs_b.pack()
        self.getVINabs_b.place(rely=vin_y, relx=0)
        getVINabs_b_ttp = CreateToolTip(self.getVINabs_b, "Read VIN from ABS module in F190.")

        self.getVINsync_b = Button(master, text="VIN SYNC", command=get_VIN_SYNC, fg="white", bg="brown", height=2, width=8, font=font1)
        self.getVINsync_b.pack()
        self.getVINsync_b.place(rely=vin_y, relx=vin_x * 5)
        getVINsync_b_ttp = CreateToolTip(self.getVINsync_b, "Read VIN from SYNC in F190.")

        self.getVINbcm_b = Button(master, text="VIN BCM", command=get_VIN_BCM, fg="white", bg="brown", height=2, width=7, font=font1)
        self.getVINbcm_b.pack()
        self.getVINbcm_b.place(rely=vin_y, relx=vin_x * 2)
        getVINbcm_b_ttp = CreateToolTip(self.getVINbcm_b, "Read VIN from BCM in F190.")

        self.getVINipc_b = Button(master, text="VIN IPC", command=get_VIN_IPC, fg="white", bg="brown", height=2, width=7, font=font1)
        self.getVINipc_b.pack()
        self.getVINipc_b.place(rely=vin_y, relx=vin_x * 3)
        getVINipc_b_ttp = CreateToolTip(self.getVINipc_b, "Read VIN from IPC in F190.")

        self.getVINrcm_b = Button(master, text="VIN RCM", command=get_VIN_RCM, fg="white", bg="brown", height=2, width=7, font=font1)
        self.getVINrcm_b.pack()
        self.getVINrcm_b.place(rely=vin_y, relx=vin_x * 4)
        getVINrcm_b_ttp = CreateToolTip(self.getVINrcm_b, "Read VIN from RCM in F190.")

        self.setFreq_b = Button(master, text="Set Freq", command=set_freq, fg="blue", bg="orange",  height=2, width=7, font=font1)
        self.setFreq_b.pack()
        self.setFreq_b.place(rely=.12, relx=.64)
        # creat tool tips here
        setFreq_b_ttp = CreateToolTip(self.setFreq_b, "Use box to enter optional frequency. If blank default used.")

        self.setVol1_b = Button(master, text="Vol=1", command=set_vol1, fg="white", bg="green", height=2, width=6, font=font1)
        self.setVol1_b.pack()
        self.setVol1_b.place(rely=volume_y, relx=0)
        setVol1_b_ttp = CreateToolTip(self.setVol1_b, "Use + and - to adjust the value of this button.")

        self.setVol5_b = Button(master, text="Vol=5", command=set_vol5, fg="white", bg="green", height=2, width=6, font=font1)
        self.setVol5_b.pack()
        self.setVol5_b.place(rely=volume_y, relx=.16)

        self.setVol16_b = Button(master, text="Vol=16", command=set_vol16, fg="white", bg="green", height=2, width=6, font=font1)
        self.setVol16_b.pack()
        self.setVol16_b.place(rely=volume_y, relx=.32)
        setVol16_b_ttp = CreateToolTip(self.setVol16_b, "Use < and > to adjust the value of this button.")

        self.setVol19_b = Button(master, text="Vol=19", command=set_vol19, fg="white", bg="green", height=2, width=6, font=font1)
        self.setVol19_b.pack()
        self.setVol19_b.place(rely=volume_y, relx=.48)

        self.setVol22_b = Button(master, text="Vol=22", command=set_vol22, fg="white", bg="green", height=2, width=6, font=font1)
        self.setVol22_b.pack()
        self.setVol22_b.place(rely=volume_y, relx=.64)

        self.setVolX_b = Button(master, text="Set VolX", command=set_volX, fg="white", bg="green", height=2, width=7, font=font1)
        self.setVolX_b.pack()
        self.setVolX_b.place(rely=volume_y, relx=.8)
        setVolX_b_ttp = CreateToolTip(self.setVolX_b, "Use slider on right to select desired value")

        self.speakerLF_b = Button(master, text="Speaker LF", command=speaker_LF, fg="white", bg="black", height=2, width=10, font=font1)
        self.speakerLF_b.pack()
        self.speakerLF_b.place(rely=speaker_y + .12, relx=speaker_x)
        speakerLF_b_ttp = CreateToolTip(self.speakerLF_b, "Enable LEFT FRONT speaker only")

        self.speakerCenter_b = Button(master, text="Speaker Center", command=speaker_Center, fg="white", bg="black", height=2, width=12, font=font1)
        self.speakerCenter_b.pack()
        self.speakerCenter_b.place(rely=speaker_y + .12, relx=speaker_x + .24)
        speakerCenter_b_ttp = CreateToolTip(self.speakerCenter_b, "Enable Center Speaker only")

        self.speakerRF_b = Button(master, text="Speaker RF", command=speaker_RF, fg="white", bg="black", height=2, width=10, font=font1)
        self.speakerRF_b.pack()
        self.speakerRF_b.place(rely=speaker_y + .12, relx=speaker_x + .52)
        speakerRF_b_ttp = CreateToolTip(self.speakerRF_b, "Enable RIGHT FRONT speaker only")

        self.speakerRR_b = Button(master, text="Speaker RR", command=speaker_RR, fg="white", bg="black", height=2, width=10, font=font1)
        self.speakerRR_b.pack()
        self.speakerRR_b.place(rely=speaker_y + .28, relx=speaker_x + .52)
        speakerRR_b_ttp = CreateToolTip(self.speakerRR_b, "Enable RIGHT REAR speaker only")

        self.speakerSub_b = Button(master, text="Speaker Sub", command=speaker_Sub, fg="white", bg="black", height=2, width=10, font=font1)
        self.speakerSub_b.pack()
        self.speakerSub_b.place(rely=speaker_y + .28, relx=speaker_x + .255)
        speakerSub_b_ttp = CreateToolTip(self.speakerSub_b, "Enable Subwoofer only")

        self.speakerLR_b = Button(master, text="Speaker LR", command=speaker_LR, fg="white", bg="black", height=2, width=10, font=font1)
        self.speakerLR_b.pack()
        self.speakerLR_b.place(rely=speaker_y + .28, relx=speaker_x)
        speakerLR_b_ttp = CreateToolTip(self.speakerLR_b, "Enable LEFT REAR speaker only")

        self.speakerAll_b = Button(master, text="Speaker ALL", command=speaker_All, fg="white", bg="black", height=2, width=10, font=font1)
        self.speakerAll_b.pack()
        self.speakerAll_b.place(rely=speaker_y + .12, relx=speaker_x + .72)
        speakerAll_b_ttp = CreateToolTip(self.speakerAll_b, "Turn all speakers on to original setting")

        self.Testerp_b = Button(master, text="TesterP On", command=testerPon, fg="blue", bg="pink")
        self.Testerp_b.pack()
        self.Testerp_b.place(rely=.71, relx=.85)

        self.TesterpOff_b = Button(master, text="TesterP Off", command=testerPoff, fg="blue", bg="pink")
        self.TesterpOff_b.pack()
        self.TesterpOff_b.place(rely=.84, relx=.80)

        self.onepress_b = Button(master, text="Start Here!", command=onepress, fg="white", bg="blue", height=2, width=10, font=font1)
        self.onepress_b.pack()
        self.onepress_b.place(rely=.12, relx=0)
        onepress_b_ttp = CreateToolTip(self.onepress_b, "Starts server, configures CAN, TP on, radio on, sets treb bass vol and freq to default")

        self.Test_b = Button(master, text="Test", command=CheckVIN, fg="blue", bg="pink")
        self.Test_b.pack()
        self.Test_b.place(rely=.9, relx=0)


class CreateToolTip(object):
    # create a tooltip for a given widget

    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)

    def enter(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left', background='yellow', relief='solid', borderwidth=1, font=("times", "10", "normal"))
        label.pack(ipadx=1)

    def close(self, event=None):
        if self.tw:
            self.tw.destroy()
# ==================================================================================================================
# ==================================================================================================================

# create global variable for the configuration file
User_Connect = False
root = Tk()
loaded_config = StringVar()
loaded_config.set('Config file not loaded!!')
e_popup = False
VIN_ecu = ""
ocolor = root.cget('bg')
info_l1 = Label(root, textvariable=loaded_config, font ="12")
info_l1.pack(side=TOP)
info_l1.place(relx=0)
default_volume = 0
# global positioning variables to make life easier
speaker_y = .47
speaker_x = .07
volume_y = .42
vin_y = .27
vin_x = .16

# volume label
loaded_volume = StringVar()
loaded_volume.set('Volume Setting = tbd')
info_l3 = Label(root, textvariable=loaded_volume, font="12")
info_l3.pack(side=TOP)
info_l3.place(relx=.65)

# Define fonts to use
font1 = font.Font(family='Helvetica', size='14')

tpid = Entry(root, bd =2, width=3)
tpid.pack()
tpid.place(rely=.76, relx=.82)
tpid_ttp = CreateToolTip(tpid, "Enter optional ECU ID for tester present on message. ex: 7DF")

fin = Entry(root, bd =2, width=4)
fin.pack()
fin.place(rely=.13, relx=.8)
fin_ttp = CreateToolTip(fin, "Enter as freq x 10: 897 for 89.7")


#vin = Entry(root, bd=2, width=2)
#vin.pack()
#vin.place(rely= speaker_y, relx=.94)
#vin_ttp = CreateToolTip(vin, "Enter volume steps 0 to 30")

v_scale = Scale(root, from_=0, to=30)
v_scale.pack()
v_scale.place(rely=speaker_y-.12, relx=.935)

tpid_off = Entry(root, bd=2, width=3)
tpid_off.pack()
tpid_off.place(rely=.92, relx=.82)
tpid_off_ttp = CreateToolTip(tpid_off, "Enter ECU ID to disable tester present message. ex: 7DF")

bass_in = Entry(root, bd=2, width=2)
bass_in.pack()
bass_in.place(rely=.21, relx=.285)
bass_in_ttp = CreateToolTip(bass_in, "Enter bass -7 to 7. Defaults to 7(max)")

treb_in = Entry(root, bd=2, width=2)
treb_in.pack()
treb_in.place(rely=.21, relx=.427)
treb_in_ttp = CreateToolTip(treb_in, "Enter treble -7 to 7. Defaults to 0(nom)")


# create a top level menu
menubar = Menu(root)
menubar.add_command(label="Quit!", command=quitme)

# add CAN setup selection to menu bar
sp_500_HS = tk.BooleanVar()
sp_500_HS.set(False)
sp_125_HS = tk.BooleanVar()
sp_125_HS.set(False)
sp_500_MS = tk.BooleanVar()
sp_500_MS.set(False)
sp_125_MS = tk.BooleanVar()
sp_125_MS.set(False)

cansp_menu = tk.Menu(menubar, background='white')
cansp_menu.add_checkbutton(label="500K on HS", onvalue=True, offvalue=False, variable=sp_500_HS, command=CAN_setup0)
cansp_menu.add_checkbutton(label="125K on HS", onvalue=True, offvalue=False, variable=sp_125_HS, command=CAN_setup1)
cansp_menu.add_checkbutton(label="500K on MS", onvalue=True, offvalue=False, variable=sp_500_MS, command=CAN_setup2)
cansp_menu.add_checkbutton(label="125K on MS", onvalue=True, offvalue=False, variable=sp_125_MS, command=CAN_setup3)
menubar.add_cascade(label='CAN Setup', menu=cansp_menu)

# add AMP setup selection to menu bar
# ECU Diagnostic Reception ID	0x0783	CAN ID for physically addressed diagnostic requests.This  parameter is only relevant, if a 11 bit identifier (=> normal addressing) is used.
# ECU Diagnostic Transmission ID	0x078B	CAN ID for physically addressed diagnostic responses.This  parameter is only relevant, if a 11 bit identifier (=> normal addressing) is used.

Amp_Present = tk.BooleanVar()
Amp_Present.set(False)

Amp_menu = tk.Menu(menubar, background='white')
Amp_menu.add_checkbutton(label="Present", onvalue=True, offvalue=False, variable=Amp_Present)
menubar.add_cascade(label='AMP', menu=Amp_menu)

# add AHU selection to menu bar
AHU_Pana = tk.BooleanVar()
AHU_Clar = tk.BooleanVar()
AHU_Vist = tk.BooleanVar()
AHU_Pana.set(True)
AHU_Clar.set(False)
AHU_Vist.set(False)

AHU_menu = tk.Menu(menubar, background='white')
AHU_menu.add_checkbutton(label="Panasonic", onvalue=True, offvalue=False, variable=AHU_Pana, command=AHU_changeP)
AHU_menu.add_checkbutton(label="Clarion", onvalue=True, offvalue=False, variable=AHU_Clar, command=AHU_changeC)
AHU_menu.add_checkbutton(label="Visteon", onvalue=True, offvalue=False, variable=AHU_Vist, command=AHU_changeV)
menubar.add_cascade(label='AHU', menu=AHU_menu)

# add Speaker Setup selection to menu bar
Speaker1 = tk.BooleanVar()
Speaker2 = tk.BooleanVar()
Speaker3 = tk.BooleanVar()

Speaker1.set(True)
Speaker2.set(False)
Speaker3.set(False)

speaker_menu = tk.Menu(menubar,background='white')
speaker_menu.add_checkbutton(label="No Tweeters", onvalue=True, offvalue=False, variable=Speaker1, command=Sp1_change)
speaker_menu.add_checkbutton(label="With Tweeters", onvalue=True, offvalue=False, variable=Speaker2, command=Sp2_change)
speaker_menu.add_checkbutton(label="Config 3", onvalue=True, offvalue=False, variable=Speaker3, command=Sp3_change)
menubar.add_cascade(label='Speakers', menu=speaker_menu)


info_l2 = Label(root, text="Connection Status = NOT CONNECTED", font="12")
info_l2.pack(side=TOP)
info_l2.place(relx=0, rely=.05)




# Check Connection Status in periodic update loop
def task():
    global e_popup
    ConfigFile.User_AMP_Selection = Amp_Present.get()
    # print("AMP present = " + str(User_AMP_Selection))
    print("User Connect = " + str(User_Connect))
    # print("OOBD Connect = " + str(OOBDControl.ConnectTest))
    if not User_Connect:
        info_l2.configure(text="Connection Status = NOT CONNECTED", fg='red')
    else:
        info_l2.configure(text="Connection Status = CONNECTED!", fg='green')

    if command_error:
        root.configure(background='red')
        if not e_popup:
              tkinter.messagebox.showinfo("CAN Error", "No response from last message request!")
        e_popup = True # show only 1 popup - no need to over do it!
    else:
        root.configure(background=ocolor)
        e_popup = False

    # check the servercmd status if showing connected - someone may have closed it then nothing will work!!
    if User_Connect:
        server_status = servercmd.poll()
        print ("Server status = " + str(server_status) + "(None = running)")
        if server_status is not None:
            # server was terminated and needs to restart
            print("Server was terminated unexpectedly!! Forcing disconnect...")
            tkinter.messagebox.showinfo("Error", "Server process was terminated unexpectedly!! Forcing disconnect...")
            disconnect()

    root.after(4000, task)  # reschedule event every 4 seconds after first call

# start the periodic check loop for first time - need this here!!
root.after(1000, task)

# add Configuration
Config_menu = tk.Menu(menubar, background='white')
for i in range(len(ConfigFile.config_list2)):
    # submenu.add_command(label=ConfigFile.config_list[i], command=lambda : ConfigSelect(selection=i))
    Config_menu.add_command(label=ConfigFile.config_list2[i]["displayname"], command=lambda s=i: ConfigSelect(selection=s))

menubar.add_cascade(label='Configuration', menu=Config_menu)

# add about item to menu bar
Help_menu = tk.Menu(menubar, background='white')
Help_menu.add_command(label="About", command=about)
Help_menu.add_command(label="Instructions", command=show_instructions)

# Help_menu.add_separator()

#submenu = Menu(Help_menu)

# automatically scroll thru the list and add to the menu the displayname
#for i in range(len(ConfigFile.config_list2)):
    # submenu.add_command(label=ConfigFile.config_list[i], command=lambda : ConfigSelect(selection=i))
 #   submenu.add_command(label=ConfigFile.config_list2[i]["displayname"], command=lambda s=i: ConfigSelect(selection=s))


#Help_menu.add_cascade(label='Configuration', menu=submenu, underline=0)
menubar.add_cascade(label='Help', menu=Help_menu)

# display the menu
root.config(menu=menubar)


# Calls the app class above
app = App(root)


# hide engineering mode things
Hide(True)


# Load the configuration file if present - needs to be done after to App(root) and Hide(True) to allow hiding/showing for the buttons
LoadConfig(ConfigFile.config_file_default)
config_file = ConfigFile.config_file_default

root.mainloop()
