import pandas as pd
import tensorflow as tf
import math, secrets
import json, ast
import numpy


KILLMAILS_URL = ""
TYPEIDTOSTRING_URL = ""
dgmTypeAttributes_PATH = "E:\project\Test1_CSV\dgmAttributeTypes_CSV\dgmTypeAttributes.csv"
dgmAttributeTypes_URL = ""


TypeAttributes_COLUMN_NAMES = ['typeID', 'attributeID',
                    'valueINT', 'valueFloat']

def get_ship_ID_Properties ():
    ship_ID_PGOutput = {}
    ship_ID_CPUOutput = {}
    ship_ID_HiSlots = {}
    ship_ID_LowSlots = {}
    ship_ID_MedSlots = {}
    ship_ID_Equipment = []
    ship_ID_EquipmentCharges = []
    TypeAttributes = pd.read_csv(dgmTypeAttributes_PATH, names=TypeAttributes_COLUMN_NAMES, header = 1)
    """Attribute Type 11 is maxPG, 12 is lowslots, 13 medslots, 14 hislots, 48 is maxCPU"""
    for index, row in TypeAttributes.iterrows():
        """ for english conversation later
            ship_IDArray[row.typeID] = """
        if (int(row.attributeID) == 11):
            
            if (math.isnan(row.valueFloat)):
                ship_ID_PGOutput[int(row.typeID)] = row.valueINT
            else:
                ship_ID_PGOutput[int(row.typeID)] = row.valueFloat

        elif (int(row.attributeID) == 12):
            
            if (math.isnan(row.valueFloat)):
                ship_ID_LowSlots[int(row.typeID)] = row.valueINT
            else:
                ship_ID_LowSlots[int(row.typeID)] = row.valueFloat
        elif (int(row.attributeID) == 13):
            if (math.isnan(row.valueFloat)):
                ship_ID_MedSlots[int(row.typeID)] = row.valueINT
            else:
                ship_ID_MedSlots[int(row.typeID)] = row.valueFloat

        elif (int(row.attributeID) == 14):
            if (math.isnan(row.valueFloat)):
                ship_ID_HiSlots[int(row.typeID)] = row.valueINT
            else:
                ship_ID_HiSlots[int(row.typeID)] = row.valueFloat
                
        elif(int(row.attributeID) == 48):
            if (math.isnan(row.valueFloat)):
                ship_ID_CPUOutput[int(row.typeID)] = row.valueINT
            else:
                ship_ID_CPUOutput[int(row.typeID)] = row.valueFloat
                """subtract equipment with PG/CPU from things with charge size except missiles or cap boosters don't have fucking charge size.
                128 charge size
                644 aimed launch
                602 things that go in cap boosters...
                1371 probe strength
                103 warp scramble range from object (disrupt probes)
                you need to search this list for every item in each killmail, and the charges list is 1/4th the size of the mod list"""
        elif (int(row.attributeID) == 128
              or int(row.attributeID) == 602
              or int(row.attributeID) == 644
              or int(row.attributeID) == 103
              or int(row.attributeID) == 1371):
            ship_ID_EquipmentCharges.append(int(row.typeID))

            """add equipment that doesn't take PG/CPU
                 169 agility modifier istabs
                150 hull hp mod (for bulkheads and expanded cargo holds)
                1076 speed for overdrive
                """ """29003 hic scram script"""
        elif (int(row.attributeID) == 50
              or int(row.attributeID) == 150
              or int(row.attributeID) == 1076
              or int(row.attributeID) == 169):
            ship_ID_Equipment.append(int(row.typeID))

        """because nanite repair paste has no properties to pick it out by"""
        ship_ID_EquipmentCharges.append(28668)
        
    ship_ID_EquipmentCharges = list(filter( lambda x: x not in ship_ID_Equipment , ship_ID_EquipmentCharges))
    ship_ID_Equipment = sorted(ship_ID_Equipment)
    """print(len(ship_ID_Equipment) , len(ship_ID_EquipmentCharges))"""
    
    ship_ID_Properties = {"PGOutput" : ship_ID_PGOutput,
                          "CPUOutput": ship_ID_CPUOutput,
                          "HiSlots": ship_ID_HiSlots,
                          "MedSlots": ship_ID_MedSlots,
                          "LowSlots": ship_ID_LowSlots,
                          "EquipmentIDs": ship_ID_Equipment,
                          "NotEquipmentIDs": ship_ID_EquipmentCharges,}
    total_slots_max = 0

    """determine the highest possible number of slots, this is a constant necessary for padding and network width"""
    for ship_ID in ship_ID_Properties["HiSlots"]:
        total_slots = ship_ID_Properties["HiSlots"][ship_ID] + ship_ID_Properties["MedSlots"][ship_ID] + ship_ID_Properties["LowSlots"][ship_ID]
        if (total_slots_max < total_slots):
            total_slots_max = int(total_slots)

            
    ship_ID_Properties["TotalSlotsMax"] = total_slots_max
    
    """print (ship_ID_Properties["NotEquipmentIDs"])"""
    
    return  ship_ID_Properties


 

def parse_Killmails (raw_killmail_PATH, ship_ID_properties):
    killmails_hi_slots = []
    killmails_med_slots = []
    killmails_low_slots = []
    killmails_all_slots = []
    ship_ID = []
    killmails = {}
    
     
    raw_killmail = pd.read_json(raw_killmail_PATH, orient='records',typ='series')
    
    for kill in raw_killmail.iteritems():
        kill = ast.literal_eval(kill[1])
        ship_low_slots = []
        ship_med_slots = []
        ship_hi_slots = []
        ship_all_slots = []
        ship_ID.append(kill["victim"]["shipTypeID"])
        """sort items by their slot, see invFlags for flag key"""
        for item in kill["items"]:
            
            if int(item["typeID"]) in ship_ID_properties["NotEquipmentIDs"]:
                """print("FILTERED")"""
                continue
            flag = int(item["flag"])
            """print (flag)"""
            if (flag > 10 and flag < 19):
                ship_low_slots.append(item["typeID"])
                ship_all_slots.append(item["typeID"])
            else:
                if (flag > 18 and flag < 27):
                    ship_med_slots.append(item["typeID"])
                    ship_all_slots.append(item["typeID"])
                else:
                    if (flag > 26 and flag < 35):
                        ship_hi_slots.append(item["typeID"])
                        ship_all_slots.append(item["typeID"])
        killmails_hi_slots.append(ship_hi_slots)
        killmails_med_slots.append(ship_med_slots)
        killmails_low_slots.append(ship_low_slots)
        killmails_all_slots.append(ship_all_slots)
    killmails = {"ShipID":ship_ID , "AllSlots": killmails_all_slots,
                "HiSlots": killmails_hi_slots, "MedSlots": killmails_med_slots,
                "LowSlots": killmails_low_slots}
    """print (killmails["AllSlots"])"""
    return killmails



"""Here we will build the training set, consisting of a ship properties (ID, PG, CPU) followed by variable length sequence of modules
ranging from 1 to the maximum number of modules each ship can have, padded with zeros to the maximum number of mods any ship can have"""
def input_evaluation_set (killmails, ship_ID_properties):
    """Load a dictionary of all relevant static properties indexed by shipID"""
    fitting_superset = []
    label_set = [0]
    fitting_superset = numpy.pad (fitting_superset,(0,ship_ID_properties["TotalSlotsMax"]), 'constant', constant_values = 0)  
    for killmail_counter in range(len(killmails["ShipID"])):
        
        """check to make sure there are any modules on the ship"""
        if len(killmails["AllSlots"][killmail_counter]) == 0:
            continue
        ship_ID = killmails["ShipID"][killmail_counter]
        
        """first three spots in the data are the static ship properties"""
        ship_subset = [int(ship_ID), int(ship_ID_properties["PGOutput"][int(ship_ID)]), int(ship_ID_properties["CPUOutput"][int(ship_ID)])]
        fitting_subset = []
        
        """print(killmails["AllSlots"][killmail_counter])"""
        item_previous = 0
        for item in killmails["AllSlots"][killmail_counter]:
            """Encode item by index in equipment list, all equipment IDs are now dense integers between 1 and the total number of equipment"""
            item = ship_ID_properties["EquipmentIDs"].index(int(item))
            
            label_set.append(int(item))
            fitting_subset.append(int(item_previous))
            fitting_subset_padded = numpy.pad (fitting_subset,(0,(ship_ID_properties["TotalSlotsMax"]- len(fitting_subset))), 'constant', constant_values = 0)
            """print(fitting_subset_padded , fitting_superset, len(fitting_subset_padded), len(fitting_superset))"""
            fitting_superset = numpy.vstack((fitting_superset , fitting_subset_padded))
            item_previous = item
            
    training_set = ship_subset, fitting_superset[:] , label_set        
    return training_set

