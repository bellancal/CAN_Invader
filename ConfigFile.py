"""
Created simple file to commonize source for the .ini file that is loaded across multiple modules
Also defines the global variables passed between modules.
This name below is the list of the available config files
User can change the one that load on program intial run by setting the index value below in the CHANGE HERE section
"""

# !!!!!!!CHANGE HERE ONLY BELOW!!!!!!
# !!!!!!!CHANGE HERE ONLY BELOW!!!!!!
# !!!!!!!CHANGE HERE ONLY BELOW!!!!!!
index = 1
# !!!!!!!CHANGE the number only using index define above !!!!!!
# !!!!!!!CHANGE HERE ONLY ABOVE!!!!!!
# !!!!!!!CHANGE HERE ONLY ABOVE!!!!!!
# !!!!!!!CHANGE HERE ONLY ABOVE!!!!!!


# DO NOT CHANGE ANYTHING BELOW.........................................
config_list2 = []  # master list of dictionary pairs - filename, displayname
config_list2.append({"filename": "oobd_control_C346.ini", "displayname": "C346"})  # index = 0 NEED TO TEST STILL!!!! TODO-test C346 vehicle
config_list2.append({"filename": "oobd_control_S550.ini", "displayname": "S550"})  # index = 1 #use ABS for VIN  500k ms, clarion, sp=2
config_list2.append({"filename": "oobd_control_B299.ini", "displayname": "B299"})  # index = 2 #use apim for VIN this worked in B299N  IPC works too.  hs 500k, visteon, sp=1
config_list2.append({"filename": "oobd_control_CD390.ini", "displayname": "CD390"})  # index = 3 NEED TO TEST STILL!!!! TODO-test CD390 Fusion vehicle
config_list2.append({"filename": "oobd_control_CD391.ini", "displayname": "CD391"})  # index = 4 NEED TO TEST STILL!!!! TODO-test CD391 vehicle
config_list2.append({"filename": "oobd_control_CD520.ini", "displayname": "CD520"})  # index = 5 use IPC for VIN on C520N or BCM OK ?, ms 125k, panasonic
config_list2.append({"filename": "oobd_control_CD539.ini", "displayname": "CD539"})  # index = 6 ms 500k, visteon, sp=1
config_list2.append({"filename": "oobd_control_V408.ini", "displayname": "V408"})  # index = 7 hs 125k, panasonic, sp=1 abs=? TODO-test other configurations of V408
config_list2.append({"filename": "oobd_control_U502.ini", "displayname": "U502"})  # index = 8 use ABS or RCM for VIN  500k ms, clarion, sp=2
config_list2.append({"filename": "oobd_control_P552.ini", "displayname": "P552"})  # index = 9 # use 500k ms, clarion, sp=2, SYNC for VIN works in the GEN1.1 GEN2/3?? ABS does NOT work!!! RCM works too
config_list2.append({"filename": "oobd_control_MKT_amp.ini", "displayname": "MKT"})  # index = 10 use 500 hs,clarion, tweeters sp=2, VIN=sync, pcm and rcm if ign  is on
config_list2.append({"filename": "test.ini", "displayname": "test only"})  # index = 10 use 500 hs,clarion, tweeters sp=2, VIN=sync, pcm and rcm if ign  is on

config_file_default = config_list2[index]["filename"]  # use index above in place of the number [x]

# Below are the global variables used for the modules in the project DO NOT CHANGE
# global User_AHU_Selection
# User_AHU_Selection = ""
# User_Speaker_Selection = ""
# User_AMP_Selection = False  # True or False
# global CFT
# CFT = config_file




