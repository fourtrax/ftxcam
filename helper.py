# -*- coding: utf-8 -*-
import pickle



defaultSettings = { "dpi" : 90,
		"operationConfig":
			{
				"operation" : "follow_path",
				"toolDiameter" : 3.4,
				"safetyHeight" : 2,	 # mm
				"feedRate" : 400,	 # mm/min
				"plungeRate" : 80,	 # mm/min
				"stepSize" : 2.5,	 # mm
				"targetDepth" : -4.9 # mm	
			}
		}
		
		
from geometry import *


def loadSettings():
	try:
		settings = pickle.load(open(".ftxcamSettings", "r"))
	except:
		saveSettings(defaultSettings)
		settings = defaultSettings
	
	return settings
		
def saveSettings(settings):
	pickle.dump(settings, open(".ftxcamSettings", "w"))
	


def mkFloat(data):
	try:
		num = float(data)
	except:
		print "Unable to convert to float: '", data,"'"
		num = 0.0

	return num