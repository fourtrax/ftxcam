# -*- coding: utf-8 -*-

from path import Line, CubicBezier, QuadraticBezier, Arc


samplingDistance = 0.05
tolerance = 0.1
minGapDistance = 0.1


class Samples(object):
	points = None
	start = None
	end = None
	totalLength = None
	
	def __init__(self, points, length):
		self.points = points
		self.start = points[0]
		self.end = points[-1]	
		self.totalLength = length
	
	def length(self):
		return self.totalLength




class Area(object):
	minX = None
	maxX = None
	minY = None
	maxY = None
	areaTable = []
	
	def __init__(self, points, analyse=True):
		"""
		 - create array with list for each x cord, contains list with y cords
		 - check if % 2 == 0 -> closed shape
		 - sort y cords
		"""
		sortedPointsX = sorted(points, key=lambda v: xCord(v))
		sortedPointsY = sorted(points, key=lambda v: yCord(v))

		self.minX = xCord(sortedPointsX[0])
		self.maxX = xCord(sortedPointsX[-1])
		self.minY = yCord(sortedPointsY[0])
		self.maxY = yCord(sortedPointsY[-1])
		self.areaTable = []
		
		print "Bounding Box: ", self.minX, self.maxX, self.minY, self.maxY
		i=-1
			
		# fill with points
		for point in sortedPointsX:
	
			if i != -1 and identicalPoint(xCord(self.areaTable[i][0]), xCord(point)):
				self.areaTable[i].append(point)
			else:
				i += 1		
				self.areaTable.append([])				
				self.areaTable[i].append(point)

		#print self.areaTable	
		
		
		
		
		gapFailureCnt = 0
		for idx in range(len(self.areaTable)):
			
			self.areaTable[idx] = sorted(self.areaTable[idx], key=lambda v: yCord(v)) # sort y cords
			
			gaps = 0 # count gaps
			#print self.areaTable[idx]
			
			yidx = 1
			while yidx < len(self.areaTable[idx]):
				
				if abs(yCord(self.areaTable[idx][yidx])-yCord(self.areaTable[idx][yidx-1])) < samplingDistance*0.9: # remove doubles
					del self.areaTable[idx][yidx]
					continue
				
				
				if abs(yCord(self.areaTable[idx][yidx])-yCord(self.areaTable[idx][yidx-1])) > minGapDistance: # find gaps
					#print "Point A: ", self.areaTable[idx][yidx-1]
					#print "Point B: ", self.areaTable[idx][yidx]
					#print "Distance: ", abs(yCord(self.areaTable[idx][yidx])-yCord(self.areaTable[idx][yidx-1]))
					gaps += 1
					
					
				yidx += 1
				
			#print "Gaps: ", gaps
			if analyse and gaps % 2 == 0 and gaps != 0:
				gapFailureCnt += 1
				
				if gapFailureCnt == 4:
					raise Exception("shape not closed...")
			else:
				gapFailureCnt = 0
			#self.areaTable[idx] = sorted(self.areaTable[idx], key=lambda v: yCord(v))
	
	
	def pointInsideLineGap(self, linePoints, point):
		
		gapId = 0
		
		for idx in range(1, len(linePoints)):
			
			if abs(yCord(linePoints[idx])-yCord(linePoints[idx-1])) > minGapDistance: #is a gap
				gapId += 1
				#print "INSIDEGAP ", gapId
				if yCord(point) < yCord(linePoints[idx]) and yCord(point) > yCord(linePoints[idx-1]) and (gapId+1)%2 == 0:
					return True
						
		return False
		
		
	def isPointInArea(self, point):
		"""
		- check bounding box first
		- find xpoint of area where point.x  distance < tolerance
		- check if y point between ys
		"""
		
		if xCord(point) > self.maxX or xCord(point) < self.minX or yCord(point) > self.maxY or yCord(point) < self.minY:
			#print "Outof Bound"
			return False
		
		#print "Detail Check"
		#print self.areaTable
		for linePoints in self.areaTable:
			#iterate over x cords
			if identicalPoint(xCord(linePoints[0]), xCord(point)):
				#same xcord here
				#print "Found identical xcord"
				if self.pointInsideLineGap(linePoints, point):
					return True
				#test if point is between y cords
				
		
		return False
				
	def checkPointIsCloseToEdge(self, point, minDistance):
		
		for linePoints in self.areaTable:
			
			if abs( xCord(linePoints[0]) - xCord(point) ) < minDistance:
				for ypoint in linePoints:
					if abs(yCord(ypoint) - yCord(point)) < minDistance:
						if distance(ypoint, point) < minDistance:
							return True
		return False


	def cleanAreaTable(self):
		
		for idx in range(len(self.areaTable)):
			
			yidx = 0
			lastPoint = None
			while yidx < len(self.areaTable[idx]):
				
				if lastPoint != None and distance(lastPoint, self.areaTable[idx][yidx]) < samplingDistance*5.0:
					lastPoint = self.areaTable[idx][yidx]
					self.areaTable[idx][yidx] = None
				else:
					lastPoint = self.areaTable[idx][yidx]
				
				yidx += 1
				
			self.areaTable[idx] = [point for point in self.areaTable[idx] if point != None]
			idx += 1
			
def getNormalVector(vectors, idx):
	
	avgPointNum = 25
	
	prevPoint = 0
	for i in range(1, avgPointNum+1):
		prevPoint += vectors[idx-i]
	prevPoint *= 1./avgPointNum
	
	
	nextPoint = 0
	for i in range(1, avgPointNum+1):
		nextPoint += vectors[idx+i] if len(vectors) > idx+i else vectors[i-1] # makes only sense if path is closed..
	nextPoint *= 1./avgPointNum
	
	#print "IDX: ", idx
	#print "prevPoint: ", prevPoint, " distance: ", abs(prevPoint-vectors[idx])
	#print "nextPoint: ", nextPoint, " distance: ", abs(prevPoint-vectors[idx])

	
	wvector = nextPoint - prevPoint

	normal =  Cords(-yCord(wvector) , xCord(wvector))
	
	normal = normal / abs(normal)
	
	return normal

def flipPathDirection(elm):
	if isinstance(elm, Line):
		elm.start, elm.end = elm.end, elm.start
		
	elif isinstance(elm, CubicBezier):
		elm.start, elm.end = elm.end, elm.start
		elm.control1, elm.control2 = elm.control2 , elm.control1
		
	elif isinstance(elm, QuadraticBezier):
		elm.start, elm.end = elm.end, elm.start

	elif isinstance(elm, Arc):
		elm.start, elm.end = elm.end, elm.start
		elm._parameterize()

	return elm


def identicalPoint(pointA, pointB, tolerance=samplingDistance*1.6):

	#print "Comparing: ", pointA, pointB
	if abs(pointA-pointB) < tolerance:
		return True
	else:
		return False


class SegmentGroup(object):
	segmentList = []
	isClosed = False
	distanceRoot = None
	curvePoints = []
	newCurvePoints = []
	operationConfig = None
	lookupData = None
	
		
	def __init__(self, elements):
		self.segmentList = elements
		
	def add(self,segment):
		self.segmentList.append(segment)
	
	def addIfConnected(self, segment):
		for elm in self.segmentList:
			if elm.start == segment.start or elm.end == segment.end:
				self.segmentList.append(segment)
				return True
		
		return False
	
	def reorder(self):		
		orderedList = [self.segmentList[0]]
		del self.segmentList[0]
		
		for i in range( len(self.segmentList) ):
			end = orderedList[-1].end
			start = self.segmentList[0].start

			
			for d in range(len(self.segmentList)):
	
				if identicalPoint(end, self.segmentList[d].start) :
					orderedList.append(self.segmentList[d])
					del self.segmentList[d]
					break
				if identicalPoint(end, self.segmentList[d].end) :
					self.segmentList[d] = flipPathDirection(self.segmentList[d])
					orderedList.append(self.segmentList[d])
					del self.segmentList[d]
					break
				
				if identicalPoint(start, self.segmentList[d].end) :
					orderedList = [self.segmentList[d]] + orderedList
					del self.segmentList[d]
					break
				if identicalPoint(start, self.segmentList[d].start) :
					self.segmentList[d] = flipPathDirection(self.segmentList[d])
					orderedList = [self.segmentList[d]] + orderedList
					del self.segmentList[d]
					break
					
			else: # loop exhausted
				# hole in path !
				self.segmentList.extend(orderedList)
				return None
	
		if len(self.segmentList) == 0 and identicalPoint(orderedList[0].start, orderedList[-1].end, tolerance=samplingDistance*3.):
			self.segmentList = orderedList
			self.isClosed = True
		else:
			self.segmentList.extend(orderedList)	
			
			
	def checkIsClosedCurve(self):
		if identicalPoint(self.curvePoints[0], self.curvePoints[-1], tolerance=samplingDistance*5.):
			self.isClosed = True

			

	
	def isClosedCurve(self):
		return self.isClosed
	
	def length(self):
		totalLength = 0
		for self.segment in self.segmentList:
			totalLength += self.segment.length()	
		
		return totalLength
	
			
	def checkPointIsCloseToEdge(self,point):

		if self.lookupData == None:
			self.lookupData = createPointLookupTable(self.curvePoints)
		
		
		if xCord(point) > self.lookupData['maxX'] or xCord(point) < self.lookupData['minX'] or yCord(point) > self.lookupData['maxY'] or yCord(point) < self.lookupData['minY']:
			return False
		

		for linePoints in self.lookupData['areaTableX']:

			if identicalPoint(xCord(linePoints[0]), xCord(point)):
				
				for ypoint in linePoints:
					if identicalPoint(yCord(ypoint), yCord(point)):
						return True

	def reverse(self):
		self.curvePoints = list(reversed(self.curvePoints))
		self.segmentList = list(reversed(self.segmentList)) # TODO: reverse path elements too
	
	def combine(self, otherSGroup, relative=-1):
		
		if relative == -1:
			self.segmentList = list(otherSGroup.segmentList) + list(self.segmentList)
			self.curvePoints = otherSGroup.curvePoints + self.curvePoints
		elif relative == 1:
			self.segmentList = list(self.segmentList) + list(otherSGroup.segmentList)
			self.curvePoints = self.curvePoints + otherSGroup.curvePoints			
		
def createPointLookupTable(points):
	
		
	sortedPointsX = sorted(points, key=lambda v: xCord(v))
	sortedPointsY = sorted(points, key=lambda v: yCord(v))

	minX = xCord(sortedPointsX[0])
	maxX = xCord(sortedPointsX[-1])
	minY = yCord(sortedPointsY[0])
	maxY = yCord(sortedPointsY[-1])
	areaTableX = []
	
	#print "Bounding Box: ", self.minX, self.maxX, self.minY, self.maxY
	i=-1
		
	# fill with points
	for point in sortedPointsX:

		if i != -1 and identicalPoint(xCord(areaTableX[i][0]), xCord(point)):
			areaTableX[i].append(point)
		else:
			i += 1		
			areaTableX.append([])				
			areaTableX[i].append(point)

	#print self.areaTable
	
	return {'areaTableX':areaTableX, 'minX':minX, 'maxX':maxX, 'minY':minY, 'maxY':maxY }
		


def Cords(x,y):
	return complex(float(x),float(y))

def Offset(x,y):
	return complex(float(x),float(y))

def xCord(cords):
	return cords.real


def yCord(cords):
	return cords.imag

def distance(a, b):
	return abs(b-a)


def getBoundingBox(points):
	
	minX = None
	minY = None
	maxX = None
	maxY = None
	
	for point in points:

		x = xCord(point)
		y = yCord(point)

		if x < minX or minX == None:
			minX = x
		if x > maxX or maxX == None:
			maxX = x
		
		if y < minY or minY == None:
			minY = y
		if y > maxY or maxY == None:
			maxY = y
			
	
	return {'minX': minX, 'minY' : minY, 'maxX' : maxX, 'maxY' : maxY}
	
	
def sampleLine(pointA, pointB, samplingDistance):
	
	vector = (pointB-pointA)
	length = abs(vector)
	vector = vector/length
	steps = int(length/samplingDistance)
	

	points = [ pointA + vector*samplingDistance * step for step in range(steps)]
	
	return points
	
	
def calcCenterPoint(points):
	center = Cords(0,0)
	
	for point in points:
		center += point
		
	
	center = center / len(points)
	
	return center



def cordsToPixmapPixel(points, float pixmapScale, float factor, int xOffset, int yOffset):
	cdef int decimalPlaces = 1
	cdef float offset = 10.
	cdef int x
	cdef int y
	pixelList = []
	pixelListWithOffset = []

	factor = factor*pixmapScale*10**decimalPlaces
	
	for point in points:
		x = int(factor*(point.real+offset))
		y = int(factor*(point.imag+offset))
		pixelList.append( (x,y) )
		pixelListWithOffset.append( (x+xOffset,y+yOffset) )

		
	return (pixelList, pixelListWithOffset)
	
	
	
def pointsAddOffset(points, float xOffset, float yOffset):
	output = []
	cdef int x
	cdef int y	
	
	for point in points:
		x = int(point[0]+xOffset)
		y = int(point[1]+yOffset)
		output.append( (x,y) )
		
	return output