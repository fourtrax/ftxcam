# -*- coding: utf-8 -*-

from Machine import Machine
from geometry import distance


def generateGcode(segmentGroups, outputFile, tolerance):

	m = Machine()

		
	
	
	for segmentGroup in reversed(segmentGroups):
		
		
		
		config = segmentGroup.operationConfig
		# Machine Settings
		safetyHeight = config['safetyHeight']	 # mm
		feedRate = config['feedRate']	 	 # mm/min
		plungeRate = config['plungeRate']	 # mm/min
		stepSize = config['stepSize']		 # mm
		targetDepth = config['targetDepth']	 # mm
		
		
		m.setFeedrate(feedRate, feedRate,  plungeRate)
		
		
		
		workingHeight = 0
		
		while workingHeight > targetDepth:
			
			workingHeight = workingHeight - stepSize
			if workingHeight < targetDepth:
				workingHeight = targetDepth
		
		
			m.moveZ(safetyHeight)
		
			
		
			
			curvePoints = segmentGroup.newCurvePoints
			
			if len(curvePoints) > 0:
				startPos = curvePoints[0]
	
				if distance( m.currentPos(), startPos) > tolerance :
					m.moveZ(safetyHeight)
	
				m.move(startPos)
				m.moveZ(workingHeight)
	
				
				for curvePoint in curvePoints:
					#TODO: arc, line optimization
					
					if distance( m.currentPos(), curvePoint) > tolerance :
						m.moveZ(safetyHeight)
										
					m.move(curvePoint)
					m.moveZ(workingHeight)
				
				
	
	m.moveZ(safetyHeight)

	gcode = m.getGcode()

	with open(outputFile, "w+") as outfile:
		outfile.write(gcode)

	print "Outputfile written !"
	
	
	
	

def generateGcodeParallel(segmentGroups, outputFile, tolerance): # not used

	m = Machine()


	config = segmentGroups[0].operationConfig
	# Machine Settings
	safetyHeight = config['safetyHeight']	 # mm
	feedRate = config['feedRate']	 # mm/min
	plungeRate = config['plungeRate']	 # mm/min
	stepSize = config['stepSize']	 # mm
	targetDepth = config['targetDepth']	 # mm
	

	workingHeight = -stepSize

	
	m.setFeedrate(feedRate, feedRate,  plungeRate)
		
	
	workingHeight = 0
	while workingHeight > targetDepth:
		
		workingHeight = workingHeight - stepSize
		if workingHeight < targetDepth:
			workingHeight = targetDepth
	
	
		m.moveZ(safetyHeight)
		
			
		for segmentGroup in segmentGroups:
			
			curvePoints = segmentGroup.newCurvePoints
			
			if len(curvePoints) > 0:
				startPos = curvePoints[0]
	
				if distance( m.currentPos(), startPos) > tolerance :
					m.moveZ(safetyHeight)
	
				m.move(startPos)
				m.moveZ(workingHeight)
	
				
				for curvePoint in curvePoints:
					#line optimization
					
					m.move(curvePoint)
				
	
	m.moveZ(safetyHeight)

	gcode = m.getGcode()

	with open(outputFile, "w+") as outfile:
		outfile.write(gcode)

	print "Outputfile written !"
	
	
	
