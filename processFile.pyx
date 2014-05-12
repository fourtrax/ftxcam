# -*- coding: utf-8 -*-
# cython: profile=False

from xml.dom import minidom
from path import Path, Line, CubicBezier, QuadraticBezier, Arc
from parser import parse_path
from helper import *
from math import ceil, cos, sin
import re
import time



	


cdef homCordsToCords(hcords):
	ncord = [b[0] for b in hcords[:-1]]
	return Cords(ncord[0], ncord[1])

cdef cordsToHomCords(cords):
	return [ (xCord(cords),), (yCord(cords),), (1,)]


cdef transformIsSimple(transformMatrix):
	
	# simple -> just translation and/or symmetrical scaling
	if transformMatrix[0][1] == transformMatrix[1][0] == 0 and 	transformMatrix[0][0] == transformMatrix[1][1]:
		return True
		
	return False

def matrixMultiply(a,b):
	zip_b = zip(*b)
	return [[sum(ele_a*ele_b for ele_a, ele_b in zip(row_a, col_b)) for col_b in zip_b] for row_a in a]



cdef parseTransform(transform_string):


	if transform_string == "":
		return None		


	transformRegex = re.compile("([\w]*)\(([^\)]*)\)")
	paramRegex = re.compile("([-+]?[0-9]*\.?[0-9]+)")
	
	transformsList = transformRegex.findall(transform_string)


	transformMatrix =  [[1.,  0,  0],
			[0,  1.,  0],
			[0,  0,  1.]]
	
	for transform in transformsList:
		operation = transform[0]
		paramList_string = transform[1]
		
		
		paramList = paramRegex.findall(paramList_string)


		if operation == "translate":
			# translate(<tx> [<ty>]), which specifies a translation by tx and ty. If <ty> is not provided, it is assumed to be zero.

			tx = float(paramList[0])
			
			ty = 0
			if len(paramList) > 1:
				ty = float(paramList[1])
			
			translate = [[1.,  0,  tx],
				   [0,  1.,  ty],
				   [0,  0,   1.]]

			transformMatrix = matrixMultiply(transformMatrix, translate)

		elif operation == "rotate":
			# rotate(<rotate-angle> [<cx> <cy>]), which specifies a rotation by <rotate-angle> degrees about a given point.
			# If optional parameters <cx> and <cy> are not supplied, the rotate is about the origin of the current user coordinate system. The operation corresponds to the matrix [cos(a) sin(a) -sin(a) cos(a) 0 0].
			# If optional parameters <cx> and <cy> are supplied, the rotate is about the point (cx, cy). The operation represents the equivalent of the following specification: translate(<cx>, <cy>) rotate(<rotate-angle>) translate(-<cx>, -<cy>).

			a = float(paramList[0])
			
			rotate = [[cos(a),   -sin(a),  0],
				[sin(a),    cos(a),  0],
				[   0,        0,	1.]]
					
			if len(paramList) == 3:
				
				cx = paramList[1]
				cy = paramList[2]
				
				moveCoordSys = [[1, 0, cx]
					      [0, 1, cy]
					      [0, 0,  1]]
				
				transformMatrix = matrixMultiply(transformMatrix, moveCoordSys)
				transformMatrix = matrixMultiply(transformMatrix, rotate)

				moveCoordSys = [[1, 0, -cx]
					      [0, 1, -cy]
					      [0, 0,  1]]
				transformMatrix = matrixMultiply(transformMatrix, moveCoordSys)
				
			else:
				transformMatrix = matrixMultiply(transformMatrix, rotate)
				
		elif operation == "scale":	
			# scale(<sx> [<sy>]), which specifies a scale operation by sx and sy. If <sy> is not provided, it is assumed to be equal to <sx>.

			sx = float(paramList[0])	
			
			sy = sx
			if len(paramList) > 1:
				sy = float(paramList[1])
			
			scale =	[[sx,  0,  0],
				 [0,  sy,  0],
				 [0,   0,  1.]]
			
			transformMatrix = matrixMultiply(transformMatrix, scale)
			
		elif operation == "xSkew":
	
			# skewX(<skew-angle>), which specifies a skew transformation along the x-axis.

			a = float(paramList[0])
			
			xSkew = [[1.,  tan(a),  0],
			         [0,     1.,    0],
			         [0,     0,    1.]]

			transformMatrix = matrixMultiply(transformMatrix, xSkew)

		elif operation == "ySkew":

			# skewY(<skew-angle>), which specifies a skew transformation along the y-axis.			
	
			a = float(paramList[0])
			
			ySkew = [[1.,       0,  0],
			         [tan(a),  1.,  0],
			         [0,       0,  1.]]

			transformMatrix = matrixMultiply(transformMatrix, ySkew)
			
		elif operation == "matrix":
			# matrix(<a> <b> <c> <d> <e> <f>), which specifies a transformation in the form of a transformation matrix of six values. matrix(a,b,c,d,e,f) is equivalent to applying the transformation matrix [a b c d e f].

			a = float(paramList[0])
			b = float(paramList[1])
			c = float(paramList[2])
			d = float(paramList[3])
			e = float(paramList[4])
			f = float(paramList[5])
			
			matrix = [[a,  c,  e],
			          [b,  d,  f],
			          [0,  0,  1.]]

			transformMatrix = matrixMultiply(transformMatrix, matrix)

		else:
			raise Exception("transform operation not found")

	return transformMatrix


cdef elmToSamples(elm):
	
	cdef int length =  elm.length()
	cdef int steps = int(ceil(length/samplingDistance))+1

	move =  1./steps

	elmPoints = []
	pos = 0				
	
	for i in range(steps):
		pos = pos + move
		
		newPoint = elm.point(pos)
		
		elmPoints.append( newPoint )
						
	if len(elmPoints) == 0:
		return None
		
	return Samples(elmPoints, length)
	
	
	
cdef applyTransform(elm, transforms):

	if elm is None:
		return None

	if transforms is None:
		return elm


	transformMatrix =  [[1,0,0],
			[0,1,0],
			[0,0,1]]
	for oneMatrix in transforms:
		if oneMatrix is None:
			continue
		transformMatrix = matrixMultiply(oneMatrix,transformMatrix)
		
		
	#print "Applying: ", transformMatrix
	
	if isinstance(elm, Line):
		if transformIsSimple(transformMatrix):
			elm.start = homCordsToCords( matrixMultiply(transformMatrix, cordsToHomCords(elm.start)) )
			elm.end = homCordsToCords( matrixMultiply(transformMatrix, cordsToHomCords(elm.end)) )
		else:
			elm = elmToSamples(elm)
			elm = applyTransform(elm, [transformMatrix])
	elif isinstance(elm, CubicBezier):
		
		if transformIsSimple(transformMatrix):
			elm.start = homCordsToCords( matrixMultiply(transformMatrix, cordsToHomCords(elm.start)) )
	
			elm.control1 = homCordsToCords( matrixMultiply(transformMatrix, cordsToHomCords(elm.control1)) )
			elm.control2 = homCordsToCords( matrixMultiply(transformMatrix, cordsToHomCords(elm.control2)) )
			elm.end = homCordsToCords( matrixMultiply(transformMatrix, cordsToHomCords(elm.end)) )
		else:
			elm = elmToSamples(elm)
			elm = applyTransform(elm, [transformMatrix])


	elif isinstance(elm, QuadraticBezier):
		
		if transformIsSimple(transformMatrix):
			elm.start = homCordsToCords( matrixMultiply(transformMatrix, cordsToHomCords(elm.start)) )
			elm.end = homCordsToCords( matrixMultiply(transformMatrix, cordsToHomCords(elm.end)) )
			elm.control1 = homCordsToCords( matrixMultiply(transformMatrix, cordsToHomCords(elm.control1)) )
		else:
			elm = elmToSamples(elm)
			elm = applyTransform(elm, [transformMatrix])			
	elif isinstance(elm, Arc):
		
		if transformIsSimple(transformMatrix):
		
			elm.start = homCordsToCords( matrixMultiply(transformMatrix, cordsToHomCords(elm.start)) )
			elm.end = homCordsToCords( matrixMultiply(transformMatrix, cordsToHomCords(elm.end)) )
		
			elm.radius = elm.radius*transformMatrix[0][0]
			
			elm._parameterize()
		else:
			elm = elmToSamples(elm)
			elm = applyTransform(elm, [transformMatrix])

		
	elif isinstance(elm, Samples):
		points = elm.points
		for idx in range(len(elm.points)):
			points[idx] = homCordsToCords( matrixMultiply(transformMatrix, cordsToHomCords(points[idx])) )
	elif isinstance(elm, Path):
		segments = elm._segments
		for idx in range(len(segments)):
			segments[idx] = applyTransform(segments[idx], [transformMatrix])
		
	else:
		raise Exception("unfortunately the element is unknown...")
		
		
		

	return elm


def parseSVG(filename):

	doc = minidom.parse(filename)

	svg_elements = doc.getElementsByTagName('svg')

	start = time.time()
	trackElements = []
	
	

	trackElements = parseElements(svg_elements[0], trackElements,transforms=[])
	print "parseElements took: ", (time.time()-start)
		
	doc.unlink()
	
	
	return trackElements


		
		
def optimizeSegmentGroups(segmentGroups):
	
	print "Before : ", len(segmentGroups)
	
	
	

	# combine segmentGroups that are next to each other
	for idx in range(1,len(segmentGroups)):

		if identicalPoint(segmentGroups[idx-1].curvePoints[-1], segmentGroups[idx].curvePoints[0]):
			segmentGroups[idx].combine(segmentGroups[idx-1], -1)
			segmentGroups[idx-1] = None

		elif identicalPoint(segmentGroups[idx-1].curvePoints[0], segmentGroups[idx].curvePoints[-1]):

			segmentGroups[idx].reverse()
			segmentGroups[idx-1].reverse()
			
			segmentGroups[idx].combine(segmentGroups[idx-1], -1)
			segmentGroups[idx-1] = None
		elif identicalPoint(segmentGroups[idx-1].curvePoints[0], segmentGroups[idx].curvePoints[0]):

			segmentGroups[idx-1].reverse()
			
			segmentGroups[idx].combine(segmentGroups[idx-1], -1)
			segmentGroups[idx-1] = None
			
		elif identicalPoint(segmentGroups[idx-1].curvePoints[-1], segmentGroups[idx].curvePoints[-1]):
			segmentGroups[idx].reverse()
						
			segmentGroups[idx].combine(segmentGroups[idx-1], -1)
			segmentGroups[idx-1] = None
	
	segmentGroups = [segmentGroup for segmentGroup in segmentGroups if segmentGroup != None]
		
	runOptimizerLoop = True
	
	while runOptimizerLoop:

		
		# reorder SegmentGroups	
		runOptimizerLoop = False
		maxSegement = len(segmentGroups)

		i=0
		while i < maxSegement-1:
			curSegmentGroup = segmentGroups[i]
			
			d = i+1
			while d < maxSegement:
				
				if identicalPoint(curSegmentGroup.curvePoints[-1], segmentGroups[d].curvePoints[0]):
					runOptimizerLoop = True					
					curSegmentGroup.combine(segmentGroups.pop(d), 1)
					maxSegement -= 1
					
				elif identicalPoint(curSegmentGroup.curvePoints[-1], segmentGroups[d].curvePoints[-1]):
					runOptimizerLoop = True
					segmentGroups[d].reverse()
					curSegmentGroup.combine(segmentGroups.pop(d), 1)					
					maxSegement -= 1
					
				elif identicalPoint(curSegmentGroup.curvePoints[0], segmentGroups[d].curvePoints[0]):
					runOptimizerLoop = True
					curSegmentGroup.reverse()
					curSegmentGroup.combine(segmentGroups.pop(d), 1)					
					maxSegement -= 1

				elif identicalPoint(curSegmentGroup.curvePoints[0], segmentGroups[d].curvePoints[-1]):
					runOptimizerLoop = True
					curSegmentGroup.reverse()
					segmentGroups[d].reverse()
					curSegmentGroup.combine(segmentGroups.pop(d), 1)					
					maxSegement -= 1
					
				
				d += 1
			
			i+=1
	
	[segmentGroup.checkIsClosedCurve() for segmentGroup in segmentGroups]
	
	print "After : ", len(segmentGroups)
	return segmentGroups

def parseElements(groupElement, trackElements, transforms):
	
	
	for child in groupElement.childNodes:
		#print child #.__dict__
		
		
		if child.nodeName == "g":
			group = child
			transform = parseTransform(group.getAttribute('transform'))
			#print "Passing Transform: ", transforms+[transform]
			
			
			trackElements = parseElements(group, trackElements, [transform]+transforms)
		else:
			
			transform = None
			elm = None
			if child.nodeType == "ELEMENT_NODE":
				transform = parseTransform(child.getAttribute('transform'))
			
			if child.nodeName == "path":
				path = child
				path_string = path.getAttribute('d')
				elm = parse_path(path_string)
				
				idx = 0
				while idx < len(elm._segments):
					if isinstance(elm._segments[idx], Line) and elm._segments[idx].start == elm._segments[idx].end:
						del elm._segments[idx]
					else:
						idx += 1
		
			elif child.nodeName == "circle":
				circle = child
				cx = circle.getAttribute("cx")
				cy = circle.getAttribute("cy")
				r = circle.getAttribute("r")
		
				elm = parse_path("M "+cx+" "+cy+" m -"+r+", 0 a "+r+","+r+" 0 1,1 "+(r * 2)+",0 a "+r+","+r+" 0 1,1 "+(-r * 2)+",0")
		
		
			elif child.nodeName == "ellipse":
				ellipse = child
				rx = ellipse.getAttribute("rx")
				ry = ellipse.getAttribute("ry")
		
				#TODO
				
			elif child.nodeName == "rect":
				rect = child
				x = float(rect.getAttribute("x"))
				y = float(rect.getAttribute("y"))
		
				width = float(rect.getAttribute("width"))
				height = float(rect.getAttribute("height"))
		
				p1 = Line( Cords(x,y), Cords(x,y+height) )
				p2 = Line( Cords(x,y+height), Cords(x+width,y+height) )
				p3 = Line( Cords(x+width,y+height), Cords(x+width,y) )
				p4 = Line( Cords(x+width,y), Cords(x,y) )
		
				elm = Path(p1, p2, p3, p4)
		
		
			elif child.nodeName == "line":
				line = child
				x1 = line.getAttribute("x1")
				y1 = line.getAttribute("y1")
				x2 = line.getAttribute("x2")
				y2 = line.getAttribute("y2")
				
				elm = Path(Line( Cords(x1,y1), Cords(x2,y2) ))
		
		
			elif child.nodeName == "polyline":
				polyline = child
				
				points = polyline.getAttribute("points")
				
				pointsList = points.split(" ")
				pathLineList = []
				
				lastPoint = None
				for point in pointsList:
					parts = point.split(",")
					if len(parts) != 2:
						continue
					(x,y) = parts
					currentPoint = Cords(x,y)
					if lastPoint != None:
						pathLineList.append(Line(lastPoint,currentPoint))
					
					lastPoint = currentPoint
				
				elm = Path(*pathLineList)
					
		
			elif child.nodeName == "polygon":
				pass
				

			if elm is not None:
				elm = applyTransform(elm, [transform]+transforms)
				trackElements.append(elm)
	



	return trackElements



def applyOperationToCurve(operation, points, settings):
	

	toolDiameter = settings['toolDiameter']
	
	normalTolerance = samplingDistance*2

	nPoints = []
	insideOnTheLeft = None

	if operation == "follow path":
		nPoints = points
		
	if operation == "profile outside" or operation == "profile inside":
		
		
		
		pointsarea = Area(points)
		
		for idx, point in enumerate(points):
			normal = getNormalVector(points, idx)
			
			if insideOnTheLeft == None:	

				
				for i in range(len(points)):
					
					#print "Point: ", points[i]
					#print "Normal 1: ", points[i]+normal*normalTolerance
					#print "Normal 2: ", points[i]-normal*normalTolerance	
							
					if pointsarea.isPointInArea(points[i]+normal*normalTolerance):
						insideOnTheLeft = True
						break
					elif pointsarea.isPointInArea(points[i]-normal*normalTolerance):
						insideOnTheLeft = False
						break
				else:
					raise Exception("Unable to find inside")
					
			if not insideOnTheLeft:
				normal = -normal

			
			
			if operation == "profile inside":
				extraDistance = toolDiameter/2.
			else:
				extraDistance = -toolDiameter/2.
			
			
			npoint = points[idx] + normal * extraDistance
			
			if not pointsarea.checkPointIsCloseToEdge(npoint, minDistance=abs(extraDistance)-5*samplingDistance): # fixes overlap at edges inside but why so much tolerance
				nPoints.append(npoint)

		

	if operation == "pocket":
		outline = applyOperationToCurve("profile inside", points, settings)
		
		if len(outline) > 0:
			pointsarea = Area(outline, analyse=False)
			pointsarea.cleanAreaTable()
	
			nPoints.extend(outline)
			
			step = int(toolDiameter/2. / samplingDistance)
			
			i = 0
			while i < len(pointsarea.areaTable):
				
				d = 0
				for d in range(1, len(pointsarea.areaTable[i])):
					
					if (d+1)%2 == 0:
						print "Line form ", pointsarea.areaTable[i][d-1], " to: ", pointsarea.areaTable[i][d]
						points = sampleLine(pointsarea.areaTable[i][d-1], pointsarea.areaTable[i][d], samplingDistance)
						nPoints.extend(points)
				
				i += step
			# do outline
			# then dvidie into lines, spacing of lines equals toolDiameter
		
	if operation == "drill":
		center = calcCenterPoint(points)
		nPoints.append(center)
		

	if operation == "none":
		nPoints = []
		

	return nPoints
	
	
	




def openSVG(filename, settings):
	
	dpi = settings['dpi'] #dpi = 90. # Dots/Inch
	dpm = dpi/25.4 # Dots/mm
	


	trackElements = parseSVG(filename)




	scale =	[[1./dpm,  0,  0],
		 [0,  1./dpm,  0],
		 [0,   	0,   1]]
	for elm in trackElements:
		applyTransform(elm, [scale])



	print "Number of Elements: ", len(trackElements)

	segmentGroups = []
	for path in trackElements:
		sg = SegmentGroup(path)
		sg.reorder()
		segmentGroups.append( sg )
	

			
	for segmentGroup in segmentGroups:
		
		segmentGroup.operationConfig = settings['operationConfig']
		
		curvePoints = []
		
		for elm in segmentGroup.segmentList:				

			
			if isinstance(elm, Samples):
				curvePoints.extend(elm.points)
				continue
			else:
				curveSteps = elm.length()/samplingDistance
				if curveSteps == 0:
					continue
	
				pos = 0				
				#print "-----"
				for i in range(int(ceil(curveSteps)+1)):
					if pos > 1: pos = 1
					
					#print pos, " ",  elm.point(pos)
					curvePoints.append(elm.point(pos))
					
					pos = pos + 1./curveSteps
				#print "-----"

		segmentGroup.curvePoints = curvePoints
	
				

	return segmentGroups
	
	

def processSVG(segmentGroups):



			
	for segmentGroup in segmentGroups:
		

		if segmentGroup.operationConfig['operation'] != "followPath" and not segmentGroup.isClosedCurve:
			raise Exception("operation requires area but just a path given")
		
		#print "applying operation: ", segmentGroup.operationConfig['operation']
		segmentGroup.newCurvePoints = applyOperationToCurve(segmentGroup.operationConfig['operation'], segmentGroup.curvePoints, segmentGroup.operationConfig)		

	



