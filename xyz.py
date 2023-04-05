from configparser import ConfigParser


# INI_FILE = "Settings.ini"              # Set .ini file name used for storing config info.
# # Load parameters from the config file
# cfg = configparser.ConfigParser()
# cfg.read(INI_FILE)
# strAdminChatID = cfg.get("tokens", "admin_chat_id") 
# print("ans-",strAdminChatID)


INI_FILE = "xyz.ini"
config = ConfigParser().read("xyz.ini")
config.read("xyz.ini")


# print(config.sections())          #['students']
# print(config["students"])         #<Section: students>
# print(config["students"]['name']) #amit
# print(list(config["students"]))   #['name', 'language', 'channel'] 


#Adding Section
# config.add_section("developer")            #this will create new section

# config.set('developer', 'name', 'Nobody')
# config.set('developer', 'tech', 'python')   #this will add key - value pair

#editing section data
# config.set('developer', 'name', 'saurabh')

#removing section element
# config.remove_option('developer','tech')

#remove section
config.remove_section('developer')

with open(INI_FILE, 'w') as file:
    config.write(file)