# -*- coding: utf-8 -*-

from helper import *


class Machine:

    currentPosition = Cords(0,0)
    currentZ = 0
    gcode = ""

    zFeedrate = 80
    xyFeedrate = xFeedrate = yFeedrate = 200

    def __init__(self):
	self.gcode += "G21 G90 G40 \r\n" # mm, absolute,  tool radius compensation off


    def moveZ(self,newZ):
        self.currentZ = newZ
        self.gcode = self.gcode + "G1 Z%f F%f \r\n" % (newZ, self.zFeedrate)

    def moveX(self,newX):
        pass

    def moveY(self,newY):
        pass


    def move(self, nPos):
        self.currentPosition = nPos
        self.gcode = self.gcode + "G1 X%.3f Y%.3f F%.3f \r\n" % (xCord(nPos)*2., yCord(nPos)*2., self.xyFeedrate)


    def setFeedrate(self,xFeedrate, yFeedrate, zFeedrate):
	self.xFeedrate = xFeedrate
	self.yFeedrate = yFeedrate
	self.zFeedrate = zFeedrate

	if xFeedrate < yFeedrate:
		self.xyFeedrate = self.xFeedrate
	else:
		self.xyFeedrate = self.yFeedrate

    def currentPos(self):
        return self.currentPosition

    def getGcode(self):
        return self.gcode