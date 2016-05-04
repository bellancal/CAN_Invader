"""
Created simple file to commonize source for the .ini file that is loaded across multiple modules
Also defines the global variables passed between modules.
This name below is the list of the available config files
User can change the one that load on program intial run by setting the index value below in the CHANGE HERE section
"""

#Change to a list structure to allow changes from gui interface
config_list = ["oobd_control_C346.ini"] # index = 0
config_list.append("oobd_control_S550.ini") # index = 1 #use ABS for VIN  ms, clarion, sp=2
config_list.append("oobd_control_B299.ini") # index = 2 #use apim for VIN this worked in B299N  cluster works too.  hs, visteon, sp=1
config_list.append("oobd_control_CD390.ini") # index = 3
config_list.append("oobd_control_CD391.ini") # index = 4
config_list.append("oobd_control_CD520.ini") # index = 5 #use IPC for VIN on C520N or BCM OK ?
config_list.append("oobd_control_CD539.ini") # index = 6 hs, visteon, sp=1
config_list.append("oobd_control_V408.ini") # index = 7  hs, panasonic, sp=1 abs=?
config_list.append("oobd_control_U502.ini") # index = 8 # use ABS for VIN  ms, clarion, sp=2
config_list.append("oobd_control_P552.ini") # index = 9 # use ms, clarion, sp=2, SYNC for VIN works in the GEN1.1 GEN2/3?? ABS does NOT work!!! RCM works too
# config_list.append("oobd_control_????.ini") # index = 10
config_list.append("test.ini") # index = last - DO NOT USE TEST ONLY

# !!!!!!!CHANGE HERE ONLY BELOW!!!!!!
# !!!!!!!CHANGE HERE ONLY BELOW!!!!!!
# !!!!!!!CHANGE HERE ONLY BELOW!!!!!!
index = 9
# !!!!!!!CHANGE the number only using index define above !!!!!!
# !!!!!!!CHANGE HERE ONLY ABOVE!!!!!!
# !!!!!!!CHANGE HERE ONLY ABOVE!!!!!!
# !!!!!!!CHANGE HERE ONLY ABOVE!!!!!!

config_file = config_list[index] # use index above in place of the number [x]

# Below are the global variables used for the modules in the project DO NOT CHANGE
global User_AHU_Selection
User_AHU_Selection = ""
User_Speaker_Selection = ""
User_AMP_Selection = False # True or False
global CFT
CFT = config_file




