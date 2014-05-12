# -*- coding: utf-8 -*-


import sys
import thread
import time
#import cProfile


try:
	import pygtk
	pygtk.require("2.0")
except:
	pass
try:
	import gtk
except:
	print("GTK Not Availible")
	sys.exit(1)


from helper import *

from processFile import openSVG,processSVG,optimizeSegmentGroups
from gcode import generateGcode

import geometry



class Gui(object):

	settings = None
	
	segmentGroups = None
	activeSegmentGroup = None
	
	groupPoints = None
	
	pixmapScale = None
	
	zoomLevel = 0
	zoomLevelFactor = 1.
	zoomLevelPixelCache = []
	maxZoomLevel = 10
	
	baseOffsetDrawingArea = (0,0)
	userOffsetDrawingArea = (0,0)
	
	drawingareaMousePressed = False
	drawingareaMouseClickPos = None
	
	def __init__(self, settings):
		gtk.threads_init()	
		self.settings = settings
		self.builder = gtk.Builder()
		self.builder.add_from_file("gui.glade")
		self.window = self.builder.get_object ("windowMain")
		if self.window:
			self.window.connect("destroy", gtk.main_quit)

		
		self.resetPixelCache()
				
		self.drawingArea = self.builder.get_object ("drawingArea")
		self.listStore = self.builder.get_object ("liststore1")
		self.treeView = self.builder.get_object ("treeviewPaths")


		
		handlers = {
		    "onDeleteWindow": gtk.main_quit,
		    "on_treeviewPaths_cursor_changed" : self.on_treeviewPaths_cursor_changed,
		    "on_drawingArea_expose_event" : self.on_drawingArea_expose_event,
		    "on_drawingArea_configure_event" : self.on_drawingArea_configure_event,
		    "on_toolbuttonOpen_clicked" : self.on_toolbuttonOpen_clicked,
		    "on_toolbuttonCalcAll_clicked" : self.on_toolbuttonCalcAll_clicked,
		    "on_toolbuttonSaveGcode_clicked" : self.on_toolbuttonSaveGcode_clicked,
		    "on_toolbuttonShowSettings_clicked" : self.on_toolbuttonShowSettings_clicked,
		    "on_windowSettings_delete_event" : self.on_windowSettings_delete_event,
		    "on_buttonSaveSettings_clicked" : self.on_buttonSaveSettings_clicked,
		    "on_pathSettings_changed" : self.on_pathSettings_changed,
		    "on_buttonCalcSinglePath_clicked" : self.on_buttonCalcSinglePath_clicked,
		    "on_drawingArea_scroll_event" : self.on_drawingArea_scroll_event,
		    "on_drawingArea_motion_notify_event" : self.on_drawingArea_motion_notify_event,
		    "on_drawingArea_button_press_event" : self.on_drawingArea_button_press_event,
		    "on_drawingArea_button_release_event" : self.on_drawingArea_button_release_event,
		    "on_menuitemAbout_button_press_event" : self.on_menuitemAbout_button_press_event,
		    "on_treeviewPaths_key_press_event" : self.on_treeviewPaths_key_press_event,
		    "on_buttonSimplifyPaths_clicked" : self.on_buttonSimplifyPaths_clicked,
		    "on_imagemenuitemNew_button_press_event" : self.on_imagemenuitemNew_button_press_event
		}
		self.builder.connect_signals(handlers)
		
		self.drawingArea.set_events(gtk.gdk.EXPOSURE_MASK | gtk.gdk.LEAVE_NOTIFY_MASK
                               				| gtk.gdk.BUTTON_PRESS_MASK
                               				| gtk.gdk.BUTTON_RELEASE_MASK
				                              | gtk.gdk.POINTER_MOTION_MASK
				                              | gtk.gdk.POINTER_MOTION_HINT_MASK )

		self.treeView.add_events(gtk.gdk.KEY_PRESS_MASK)

	def resetPixelCache(self):
		self.pixmapScale = None
		self.zoomLevelPixelCache = [None for i in range(2*self.maxZoomLevel+1)]

	def on_pathSettings_changed(self, widget):

		toolDiameter = mkFloat(self.builder.get_object ("entryToolDiameter").get_text())
		safetyHeight = mkFloat(self.builder.get_object ("entrySafetyHeight").get_text())
		feedRate = mkFloat(self.builder.get_object ("entryFeedrate").get_text())
		plungeRate = mkFloat(self.builder.get_object ("entryPlungeRate").get_text())
		stepSize = mkFloat(self.builder.get_object ("entryStepSize").get_text())
		targetDepth = mkFloat(self.builder.get_object ("entryTargetDepth").get_text())
		
		operationComboBox = self.builder.get_object ("comboboxOperation")
		index = operationComboBox.get_active()
		model = operationComboBox.get_model()
		item = model[index]
		
		newConfig = {
			"toolDiameter" : toolDiameter,
			"safetyHeight" : safetyHeight,
			"feedRate" : feedRate,
			"plungeRate" : plungeRate,
			"stepSize" : stepSize,
			"targetDepth" : targetDepth,
			"operation" : item[0]
		}
		
		print "Setting did change !!!!!"

		self.segmentGroups[self.activeSegmentGroup].operationConfig = newConfig

		return True

	def on_imagemenuitemNew_button_press_event(self, menu, widget):
		
		self.segmentGroups = None
		self.activeSegmentGroup = None
		
		self.groupPoints = None
		
		self.pixmapScale = None
		
		self.zoomLevel = 0
		self.zoomLevelFactor = 1.
		self.zoomLevelPixelCache = []
		self.maxZoomLevel = 10
		
		self.baseOffsetDrawingArea = (0,0)
		self.userOffsetDrawingArea = (0,0)
		
		self.drawingareaMousePressed = False
		self.drawingareaMouseClickPos = None
		
		self.redraw_drawingArea()
		self.refreshListElements()

	
	def on_treeviewPaths_cursor_changed(self, widget):

		
		treeviewPaths = self.builder.get_object ("treeviewPaths")
		idx = None
		(model, pathlist) = treeviewPaths.get_selection().get_selected_rows()
		for path in pathlist :
			tree_iter = model.get_iter(path)
			
			idx = model.get_value(tree_iter,1)

		if idx is None:
			return
		
		propertiesTable = self.builder.get_object ("propertiesTable")
		propertiesTable.show()


		self.activeSegmentGroup = idx
		config = self.segmentGroups[idx].operationConfig

		self.builder.get_object("entryToolDiameter").set_text(str(config['toolDiameter']))
		self.builder.get_object("entrySafetyHeight").set_text(str(config['safetyHeight']))
		self.builder.get_object("entryFeedrate").set_text(str(config['feedRate']))
		self.builder.get_object("entryPlungeRate").set_text(str(config['plungeRate']))
		self.builder.get_object("entryStepSize").set_text(str(config['stepSize']))
		self.builder.get_object("entryTargetDepth").set_text(str(config['targetDepth']))
		
		operationComboBox = self.builder.get_object ("comboboxOperation")
		model = operationComboBox.get_model()
		for idx, item in enumerate(model):
			if item[0] == config['operation']:
				operationComboBox.set_active(idx)


		#print "---"
		#print "start: ", self.segmentGroups[self.activeSegmentGroup].curvePoints[0]
		#print "end: ", self.segmentGroups[self.activeSegmentGroup].curvePoints[-1]
		#print "---"
		
		
		self.redraw_drawingArea()
		# highlight path
		self.drawCurveOnTop(self.segmentGroups[self.activeSegmentGroup].curvePoints, color="#0000FF")
		


	def on_buttonSimplifyPaths_clicked(self, widget):
		self.segmentGroups = optimizeSegmentGroups(self.segmentGroups)
		self.refreshListElements()


	def on_treeviewPaths_key_press_event(self, widget, event):

		if event.keyval == gtk.keysyms.Delete:
			print "deleting element"
			del self.segmentGroups[self.activeSegmentGroup]
			self.resetPixelCache()

			self.refreshListElements()
			
		
		
	def on_menuitemAbout_button_press_event(self, widget, event):
		aboutdialog = gtk.AboutDialog()
		aboutdialog.set_name("ftxcam")
		aboutdialog.set_version("0.1")
		aboutdialog.set_comments("simpel cam software, generates gcode from svg files")
		aboutdialog.set_website("http://ftx.ionscale.com")
		aboutdialog.set_website_label("website")
		aboutdialog.set_authors([ "Gerrit Wyen <gerrit@ionscale.com>"])

		aboutdialog.set_transient_for(self.window)

		aboutdialog.run()
		aboutdialog.destroy()
				
	def on_drawingArea_motion_notify_event(self, widget, event):
		
		if self.drawingareaMousePressed != False:			
			self.userOffsetDrawingArea = ( int(-(self.drawingareaMouseClickPos[0]-event.x)+self.baseOffsetDrawingArea[0]),
						 int( -(self.drawingareaMouseClickPos[1]-event.y)+self.baseOffsetDrawingArea[1]) )
			self.redraw_drawingArea()
			
		
	def on_drawingArea_button_press_event(self, widget, event):
		print widget
		print event
		print "POS: ", event.x, " ", event.y
		print "button press event"
		
		self.drawingareaMousePressed = True
		
		cursor = gtk.gdk.Cursor(gtk.gdk.FLEUR)
		widget.window.set_cursor(cursor)

			
		self.baseOffsetDrawingArea = self.userOffsetDrawingArea
		self.drawingareaMouseClickPos = (event.x, event.y)
		
		#treeviewPaths = self.builder.get_object ("treeviewPaths")
		#cords = self.pixmapPixelToCords(event.x, event.y)
		#
		#for idx, segmentGroup in enumerate(segmentGroups):
			#if segmentGroup.checkPointIsCloseToEdge(cords):
				#
				#treeviewPaths.set_cursor( treeviewPaths.get_path_at_pos(idx, 0) )
				#on_treeviewPaths_cursor_changed(None)
				#
				#break

	def on_drawingArea_button_release_event(self, widget, event):
		print "button press release"

		self.drawingareaMousePressed = False
		widget.window.set_cursor(None)

		

	def on_drawingArea_scroll_event(self, widget, event):

		if event.direction == gtk.gdk.SCROLL_DOWN:
			self.zoomLevel -= 1
		if event.direction == gtk.gdk.SCROLL_UP:
			self.zoomLevel += 1

		if self.zoomLevel < -self.maxZoomLevel:
			self.zoomLevel = -self.maxZoomLevel
		elif  self.zoomLevel > self.maxZoomLevel:
			self.zoomLevel = self.maxZoomLevel

			

		
		if self.zoomLevel < 0:
			self.zoomLevelFactor = (1.-abs(self.zoomLevel)*0.1)
		if self.zoomLevel == 0:
			self.zoomLevelFactor = 1.
		if self.zoomLevel > 0:
			self.zoomLevelFactor = (self.zoomLevel*0.1+1.)

		print "New Zoom Level: ", self.zoomLevel, " Factor: ", self.zoomLevelFactor

			
		self.redraw_drawingArea()

	def on_buttonCalcSinglePath_clicked(self, widget):
		self.indicateLoading(True)
		
		thread.start_new_thread(self.processSVG_Thread, ([self.segmentGroups[self.activeSegmentGroup] ],))

		
	def on_toolbuttonShowSettings_clicked(self, widget):
		
		self.builder.get_object("entrySvgDpiGS").set_text( str(self.settings['dpi']))
		self.builder.get_object("entryToolDiameterGS").set_text(str(self.settings['operationConfig']['toolDiameter']))
		self.builder.get_object("entrySafetyHeightGS").set_text(str(self.settings['operationConfig']['safetyHeight']))
		self.builder.get_object("entryFeedrateGS").set_text(str(self.settings['operationConfig']['feedRate']))
		self.builder.get_object("entryPlungeRateGS").set_text(str(self.settings['operationConfig']['plungeRate']))
		self.builder.get_object("entryStepSizeGS").set_text(str(self.settings['operationConfig']['stepSize']))
		self.builder.get_object("entryTargetDepthGS").set_text(str(self.settings['operationConfig']['targetDepth']))
		
		operationComboBox = self.builder.get_object ("comboboxOperationGS")
		model = operationComboBox.get_model()
		for idx, item in enumerate(model):
			if item[0] == self.settings['operationConfig']['operation']:
				operationComboBox.set_active(idx)
		
		
	
		
		self.builder.get_object ("windowSettings").show()
		
	def on_windowSettings_delete_event(self, widget, smth):
		self.builder.get_object ("windowSettings").hide()
		
		return True # avoid destruction
	
	def on_buttonSaveSettings_clicked(self, widget):
		
		dpi = int( self.builder.get_object("entrySvgDpiGS").get_text() )
		toolDiameter = float(self.builder.get_object ("entryToolDiameterGS").get_text())
		safetyHeight = float(self.builder.get_object ("entrySafetyHeightGS").get_text())
		feedRate = float(self.builder.get_object ("entryFeedrateGS").get_text())
		plungeRate = float(self.builder.get_object ("entryPlungeRateGS").get_text())
		stepSize = float(self.builder.get_object ("entryStepSizeGS").get_text())
		targetDepth = float(self.builder.get_object ("entryTargetDepthGS").get_text())
		
		operationComboBox = self.builder.get_object ("comboboxOperationGS")
		index = operationComboBox.get_active()
		model = operationComboBox.get_model()
		item = model[index]
		
		newSettings = {"dpi" : dpi,
		"operationConfig": {
			"toolDiameter" : toolDiameter,
			"safetyHeight" : safetyHeight,
			"feedRate" : feedRate,
			"plungeRate" : plungeRate,
			"stepSize" : stepSize,
			"targetDepth" : targetDepth,
			"operation" : item[0]
			}
		}
		
		self.settings = newSettings
		saveSettings(newSettings)
		
		self.builder.get_object ("windowSettings").hide()


	def indicateLoading(self, isLoading):
		
		if isLoading:	
			self.builder.get_object ("hboxLoadingIndicator").show_now()
		else:
			self.builder.get_object ("hboxLoadingIndicator").hide()
		
		gtk.main_iteration(block=False)
		
		
	def on_toolbuttonOpen_clicked(self, widget):

	
		# file chooser start
	
		dialog = gtk.FileChooserDialog("Open..",
		                               None,
		                               gtk.FILE_CHOOSER_ACTION_OPEN,
		                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
		                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		
		filefilter = gtk.FileFilter()
		filefilter.set_name("All files")
		filefilter.add_pattern("*")
		dialog.add_filter(filefilter)
		
		filefilter = gtk.FileFilter()
		filefilter.set_name("Images")
		filefilter.add_mime_type("image/svg")
		filefilter.add_pattern("*.svg")
		dialog.add_filter(filefilter)
		
		svgFilename = ""
		response = dialog.run()
		if response == gtk.RESPONSE_OK:
			svgFilename = dialog.get_filename()
			dialog.destroy()
			print svgFilename, 'selected'
		elif response == gtk.RESPONSE_CANCEL:
			print 'Closed, no files selected'
			dialog.destroy()
			return
		
		if svgFilename == "":
			return

		# file chooser end

		gtk.main_iteration(block=False)
		
		self.indicateLoading(True)
		thread.start_new_thread(self.openSVG_Thread, (svgFilename,))



	
	def openSVG_Thread(self, svgFilename):
	
		gtk.threads_enter()
		self.resetPixelCache()
		propertiesTable = self.builder.get_object ("propertiesTable")
		propertiesTable.hide()
				
		self.segmentGroups = openSVG(svgFilename, self.settings)
		#cProfile.runctx('self.segmentGroups = openSVG(svgFilename, self.settings)', globals(), locals(),filename='ftxcamstats')

		
		self.zoomLevel = 0	
		self.resetPixelCache()
	
		self.refreshListElements()

		self.indicateLoading(False)
		gtk.threads_leave()
		
	def refreshListElements(self):
		self.clearListElements()
		
		if self.segmentGroups:
			groupPoints = []
			segmentGroupDesc = []
			for idx, group in enumerate(self.segmentGroups):
				segmentGroupDesc.append( ("Path " + str(idx) + " (%.2f)" % group.length(), str( group.isClosedCurve() )) )
				groupPoints.extend(group.curvePoints)
	
			self.groupPoints = groupPoints
		
		
			self.addListElements(segmentGroupDesc)

		self.redraw_drawingArea()

		

		
	def on_toolbuttonCalcAll_clicked(self, widget):

		if self.segmentGroups:
			self.indicateLoading(True)
					
			thread.start_new_thread(self.processSVG_Thread, (self.segmentGroups,))

	def processSVG_Thread(self, segmentGroups):
		gtk.threads_enter()
		processSVG(segmentGroups)
		
		self.redraw_drawingArea()
		self.indicateLoading(False)
		gtk.threads_leave()
		
	def on_toolbuttonSaveGcode_clicked(self, widget):
		
		if not self.segmentGroups:
			return		
		
		# file saver start
	
		dialog = gtk.FileChooserDialog("Save..",
		                               None,
		                               gtk.FILE_CHOOSER_ACTION_SAVE,
		                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
		                                gtk.STOCK_SAVE, gtk.RESPONSE_OK))
		dialog.set_default_response(gtk.RESPONSE_OK)
		

		
		filefilter = gtk.FileFilter()
		filefilter.set_name("Gcode")
		filefilter.add_mime_type("text/gcode")
		filefilter.add_pattern("*.gcode")
		dialog.add_filter(filefilter)
		
		response = dialog.run()
		if response == gtk.RESPONSE_OK:
			gcodeFilename = dialog.get_filename()
			dialog.destroy()
			print gcodeFilename, 'selected'
		elif response == gtk.RESPONSE_CANCEL:
			print 'Closed, no filename given'
			dialog.destroy()
			return
			
		if gcodeFilename == "":
			return
		
		# file saver end

		gtk.main_iteration(block=False)

		self.indicateLoading(True)
		thread.start_new_thread(self.generateGcode_Thread, (gcodeFilename, tolerance,))

	def generateGcode_Thread(self, gcodeFilename, tolerance):
		
		generateGcode(self.segmentGroups, gcodeFilename, tolerance)
		
		gtk.threads_enter()
		self.indicateLoading(False)
		gtk.threads_leave()
		
	
	def addListElements(self,pathList):

		for idx, path in enumerate(pathList):
			self.listStore.append([path[0], idx, path[1]])


	def clearListElements(self):
		self.listStore.clear()


	def newColorGC(self, color):
		gc = self.window.window.new_gc()
		gc.set_rgb_fg_color(gtk.gdk.color_parse(color))

		return gc
	

	
	def cordsToPixmapPixel(self, point, noOffset=False, userOffset=(0,0)):
		decimalPlaces = 1
		offset = 10.
		
		if noOffset:
			offset = 0
		
		pixmapScale = self.pixmapScale
		factor = self.zoomLevelFactor


		x = int(factor*pixmapScale* (xCord(point)+offset) * 10**decimalPlaces)
		y = int(factor*pixmapScale* (yCord(point)+offset) * 10**decimalPlaces)
		
		return [x+userOffset[0],y+userOffset[1]]
		
		

	def drawCoordinateSystem(self):
		
		(pixelCordsRootX, pixelCordsRootY)  = self.cordsToPixmapPixel(Cords(0,0))
		pixelCordsRootX += self.userOffsetDrawingArea[0]
		pixelCordsRootY += self.userOffsetDrawingArea[1]

		gc = self.newColorGC("#FF0000")
		(pixelCordsEndX, pixelCordsEndY) = self.cordsToPixmapPixel(Cords(10,0))
		arrowSize = int(pixelCordsEndX*0.03)

		pixelCordsEndX += self.userOffsetDrawingArea[0]
		pixelCordsEndY += self.userOffsetDrawingArea[1]
		
		self.drawingAreaPixmap.draw_line(gc, pixelCordsRootX, pixelCordsRootY, pixelCordsEndX, pixelCordsEndY)
		
		points = [(pixelCordsEndX, pixelCordsEndY), (pixelCordsEndX-arrowSize, pixelCordsEndY-arrowSize), (pixelCordsEndX-arrowSize, pixelCordsEndY+arrowSize)]
		self.drawingAreaPixmap.draw_polygon(gc, True, points)
		
		
		gc = self.newColorGC("#00FF00")
		(pixelCordsEndX, pixelCordsEndY) = self.cordsToPixmapPixel(Cords(0,10))
		pixelCordsEndX += self.userOffsetDrawingArea[0]
		pixelCordsEndY += self.userOffsetDrawingArea[1]
		self.drawingAreaPixmap.draw_line(gc, pixelCordsRootX, pixelCordsRootY, pixelCordsEndX, pixelCordsEndY)

		points = [(pixelCordsEndX, pixelCordsEndY), (pixelCordsEndX-arrowSize, pixelCordsEndY-arrowSize), (pixelCordsEndX+arrowSize, pixelCordsEndY-arrowSize)]
		self.drawingAreaPixmap.draw_polygon(gc, True, points)
		

	def drawCurve(self, curvePoints):
		
		if curvePoints == None:
			return
			
		
		start = time.time()
		(pixelList, pixelListWithOffset) = geometry.cordsToPixmapPixel(curvePoints, self.pixmapScale, self.zoomLevelFactor, self.userOffsetDrawingArea[0], self.userOffsetDrawingArea[1])
		print "Map took: ", (time.time()-start)


		start = time.time()
		style = self.window.get_style()
		self.drawingAreaPixmap.draw_points(style.black_gc, pixelListWithOffset)
		print "Draw took: ", (time.time()-start)

	
		
		
		self.drawingArea.queue_draw()
		
		return pixelList
		
		
	def drawCurveFromCache(self, pixelList):
		start = time.time()
	
		style = self.window.get_style()
		pixelList = geometry.pointsAddOffset(pixelList, self.userOffsetDrawingArea[0], self.userOffsetDrawingArea[1])
		self.drawingAreaPixmap.draw_points(style.black_gc, pixelList)

		print "Draw took: ", (time.time()-start)


		
	def drawCurveOnTop(self, curvePoints, color="#FF0AA0"):
	
		if curvePoints == None:
			return
		
		pixelList = []
		lastCords = (None, None)
		for point in curvePoints:

			(x,y) = self.cordsToPixmapPixel(point)
			if lastCords == (x,y):
				continue
			
			pixelList.append( (int(x+self.userOffsetDrawingArea[0]), int(y+self.userOffsetDrawingArea[1])) )

			
			lastCords = (x,y)
			
		gc = self.newColorGC(color)
		self.drawingAreaPixmap.draw_points(gc, pixelList)

		self.drawingArea.queue_draw()
		
		return pixelList
		
	def redraw_drawingArea(self):
		(pixmap_width, pixmap_height) = self.drawingAreaPixmap.get_size()

		self.drawingAreaPixmap.draw_rectangle(self.window.get_style().white_gc,True, 0, 0, pixmap_width, pixmap_height)
	
		
		
		
		if self.segmentGroups != None and len(self.segmentGroups) > 0:
		
			if self.pixmapScale is None:
				decimalPlaces = 1
			
				bounds = getBoundingBox(self.groupPoints)
				
				width = int(bounds['maxX']*10**decimalPlaces*1.5)
				height = int(bounds['maxY']*10**decimalPlaces*1.5)
				
					
				scaleX = pixmap_width/float(width)
				scaleY = pixmap_height/float(height)
				
				self.pixmapScale = scaleX if scaleX < scaleY else scaleY

			self.drawGrid()
			
			if self.zoomLevelPixelCache[self.zoomLevel+self.maxZoomLevel] != None:
				self.drawCurveFromCache(self.zoomLevelPixelCache[self.zoomLevel+self.maxZoomLevel])
			else:
				self.zoomLevelPixelCache[self.zoomLevel+self.maxZoomLevel] = self.drawCurve(self.groupPoints)
				
			
			for segmentGroup in self.segmentGroups:
				if len(segmentGroup.newCurvePoints) != 0:
					self.drawCurveOnTop(segmentGroup.newCurvePoints)
					
					if segmentGroup.operationConfig['operation'] == "drill": # draw cross
						
						self.drawDrillMark(segmentGroup.newCurvePoints[0], segmentGroup.operationConfig['toolDiameter']/2.)
	
					
					
						
			
			self.drawCoordinateSystem()
		self.drawingArea.queue_draw()
	
	def drawDrillMark(self, center, radius):
		
		gc = self.newColorGC("#FF0AA0")
		
		radiusVec = self.cordsToPixmapPixel(Cords(radius, radius), True)
		center = Cords(xCord(center), yCord(center))

		centerPoint = self.cordsToPixmapPixel(center, False, self.userOffsetDrawingArea)

		
		edgePoint = self.cordsToPixmapPixel(center+Cords(radius, radius), False,  self.userOffsetDrawingArea)
		self.drawingAreaPixmap.draw_line(gc, centerPoint[0], centerPoint[1], edgePoint[0], edgePoint[1])
		
		edgePoint = self.cordsToPixmapPixel(center-Cords(radius, radius), False,  self.userOffsetDrawingArea)
		self.drawingAreaPixmap.draw_line(gc, centerPoint[0], centerPoint[1], edgePoint[0], edgePoint[1])
		self.drawingAreaPixmap.draw_arc(gc, False, edgePoint[0], edgePoint[1], radiusVec[0]*2, radiusVec[1]*2, 0, 360*64)		
		
		edgePoint = self.cordsToPixmapPixel(center+Cords(radius, -radius), False, self.userOffsetDrawingArea)
		self.drawingAreaPixmap.draw_line(gc, centerPoint[0], centerPoint[1], edgePoint[0], edgePoint[1])

		edgePoint = self.cordsToPixmapPixel(center-Cords(radius, -radius), False, self.userOffsetDrawingArea)
		self.drawingAreaPixmap.draw_line(gc, centerPoint[0], centerPoint[1], edgePoint[0], edgePoint[1])
		
		self.drawingArea.queue_draw()
	
	
	def drawGrid(self):
		workareaWidth = 500
		workareaHeight = 500
		gridSize = 10.
		
		gc = self.newColorGC("#AAAAAA")
		gc = self.newColorGC("#D3D3D3")
		
		for i in range(0, int(workareaWidth/gridSize)+1):
			x = int(i*gridSize)

			start = self.cordsToPixmapPixel(Cords(x, 0), False, self.userOffsetDrawingArea)
			end = self.cordsToPixmapPixel(Cords(x, workareaHeight), False, self.userOffsetDrawingArea)
			
			self.drawingAreaPixmap.draw_line(gc, start[0], start[1], end[0], end[1])

		for i in range(0, int(workareaHeight/gridSize)+1):
			y = int(i*gridSize)

			start = self.cordsToPixmapPixel(Cords(0, y), False, self.userOffsetDrawingArea)
			end = self.cordsToPixmapPixel(Cords(workareaWidth, y), False, self.userOffsetDrawingArea)
			
			self.drawingAreaPixmap.draw_line(gc, start[0], start[1], end[0], end[1])

	
	# create new pixmap for drawing area
	def on_drawingArea_configure_event(self, widget, event):
	
		self.resetPixelCache()
		
		x, y, width, height = widget.get_allocation()
		self.drawingAreaPixmap = gtk.gdk.Pixmap(widget.window, width, height)
	
		self.redraw_drawingArea()
			
		return True


	# redraw screen from pixmap
	def on_drawingArea_expose_event(self,widget, event):
		x , y, width, height = event.area
		widget.window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL], self.drawingAreaPixmap, x, y, x, y, width, height)
		return False

	def quit(self, widget):
		sys.exit(0)
		
		
	def runMainLoop(self):
		self.window.show()
		propertiesTable = self.builder.get_object ("propertiesTable")
		propertiesTable.hide()
		
		gtk.main()
		

	
	def runMainLoopBackground(self):
		thread.start_new_thread(self.runMainLoop, ())




