#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Gerrit Wyen <gerrit@ionscale.com>"
__license__ = "GNU General Public License v2 or later (GPLv2+)"


from Gui import Gui
from helper import loadSettings






if __name__=="__main__":
	
	
	settings = loadSettings()
	
	camgui = Gui(settings)
	
	camgui.runMainLoop()

