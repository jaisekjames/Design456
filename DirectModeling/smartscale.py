# -*- coding: utf-8 -*-
from __future__ import unicode_literals
#
# ***************************************************************************
# *                                                                        *
# * This file is a part of the Open Source Design456 Workbench - FreeCAD.  *
# *                                                                        *
# * Copyright (C) 2021                                                     *
# *                                                                        *
# *                                                                        *
# * This library is free software; you can redistribute it and/or          *
# * modify it under the terms of the GNU Lesser General Public             *
# * License as published by the Free Software Foundation; either           *
# * version 2 of the License, or (at your option) any later version.       *
# *                                                                        *
# * This library is distributed in the hope that it will be useful,        *
# * but WITHOUT ANY WARRANTY; without even the implied warranty of         *
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU      *
# * Lesser General Public License for more details.                        *
# *                                                                        *
# * You should have received a copy of the GNU Lesser General Public       *
# * License along with this library; if not, If not, see                   *
# * <http://www.gnu.org/licenses/>.                                        *
# *                                                                        *
# * Author : Mariwan Jalal   mariwan.jalal@gmail.com                       *
# **************************************************************************

import os,sys
import FreeCAD as App
import FreeCADGui as Gui
import Draft
import Part
from pivy import coin
import FACE_D as faced
import math as _math
from PySide.QtCore import QT_TRANSLATE_NOOP
import ThreeDWidgets.fr_line_widget as wlin
import ThreeDWidgets.fr_coinwindow  as win
from typing import ItemsView, List
import time 
import Design456Init
from ThreeDWidgets.constant import FR_COLOR
SeperateLinesFromObject=4
from PySide import QtGui,QtCore
from ThreeDWidgets.fr_arrow_widget import Fr_Arrow_Widget

def smartLinecallback(smartLine,obj,parentlink):
    """
        Calback when line is clicked
    """    
    pass 
    
def smartlbl_callback(smartLine,obj,parentlink):
    """
        callback when label is double clicked
    """
    print("smartline lbl callback") 
    #clone the object
    p1=smartLine.w_vector[0]
    p2=smartLine.w_vector[1]
    deltaX= p2.x-p1.x
    deltaY= p2.y-p1.y
    deltaZ= p2.z-p1.z
    side=None
    oldv=float(smartLine.w_label[0])
    if deltaX==0 and deltaZ==0:
        side= 'y'
    elif deltaY==0.0 and deltaZ==0.0:
        side='x'
    elif deltaY==0.0 and deltaX==0.0 and deltaZ!=0.0:
        side='z'
    newValue=0
    #all lines has a 4 mm more size due to the way we calculate them. Remove that
    newValue=faced.GetInputValue(oldv).getDoubleValue()
    if newValue==0 or newValue==None:
        #User canceled the value
        return -1

    if obj==None:
        # Only one object must be selected
        errMessage = "Select an object to scale"
        faced.getInfo().errorDialog(errMessage)
        return
    
    cloneObj = Draft.clone(obj, forcedraft=True)
    scaleX=1
    scaleY=1
    scaleZ=1    

    if side=='y':
        scaleY=newValue/(deltaY-SeperateLinesFromObject)
    elif side=='x':
        scaleX=newValue/(deltaX-SeperateLinesFromObject)
    elif side=='z':
        scaleZ=newValue/deltaZ
    else : 
        print("error")
    try:
        
        cloneObj.Scale=App.Vector(scaleX,scaleY,scaleZ)

        obj.Visibility=False
        App.ActiveDocument.recompute()
        _name=obj.Label
        obj.Label=obj.Label+"old"
        __shape = Part.getShape(cloneObj,'',needSubElement=False,refine=False)
        _simpleCopy=App.ActiveDocument.addObject('Part::Feature',_name)
        _simpleCopy.Shape=__shape
        App.ActiveDocument.recompute()
        App.ActiveDocument.removeObject(obj.Name)
        App.ActiveDocument.removeObject(cloneObj.Name)
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(_simpleCopy)
        _simpleCopy.Label = _name        
        App.ActiveDocument.recompute()
        #All objects must get link to the new targeted object
        (_vectors,_lengths)=parentlink.returnVectorsFromBoundaryBox(_simpleCopy)
        tt=0
        for i in range (0,3):
            parentlink.smartInd[i].set_target(_simpleCopy)
            parentlink.smartInd[i].w_vector=_vectors[i]
            parentlink.smartInd[i].changeLabelfloat(_lengths[i])
            parentlink.smartInd[i].redraw()        #Update the vertices here
        App.ActiveDocument.recompute()

    except Exception as err:
        App.Console.PrintError("'Design456_SmartScale' Failed. "
                               "{err}\n".format(err=str(err)))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


class smartLines(wlin.Fr_Line_Widget):
    """
        A subclass of fr_line_widget used to show 
        the length,width and height of the selected
        object for scaling. 
    """
    def __init__(self, vectors: List[App.Vector] = [], label: str = "", lineWidth=1,linkToParent=None):
        super().__init__(vectors, label,lineWidth)     #Must be done first as described in fr_line_widget
        self.w_lbl_calback_=smartlbl_callback
        self.w_callback_=smartLinecallback
        self.targetObject=None
        #Todo: Which color? black is good?
        #self.w_color=FR_COLOR.FR_GREEN
        self._parentLink=linkToParent  #this hold the command class. used to reproduce the whole object.
 
    def do_callback(self):
        """ Do widget callback"""
        self.w_callback_(self,self.targetObject,self._parentLink)
        
    def do_lblcallback(self):
        """ Do label callaback"""
        self.w_lbl_calback_(self,self.targetObject,self._parentLink)

    def set_target(self,target):
        """ Set target object"""
        self.targetObject=target

class Design456_SmartScale:
    """
        Resize any 3D object by resizing each sides (x,y,z)
        Simple and interactive way to resize precisely any shape.
    """
    _mywin=None
    smartInd=[]
    dialog=None
    tab=None
    mw=None
    def returnVectorsFromBoundaryBox(self,selected):
        #Max object length in all directions        
        lengthX =selected.Shape.BoundBox.XLength
        lengthY =selected.Shape.BoundBox.YLength
        lengthZ =selected.Shape.BoundBox.ZLength

        #Make the end 2 mm longer/after the object
        NewX= selected.Shape.BoundBox.XMax+SeperateLinesFromObject/2
        NewY= selected.Shape.BoundBox.YMax+SeperateLinesFromObject/2
        NewZ= selected.Shape.BoundBox.ZMax

        #Make the start 2 mm before the object is placed
        startX= selected.Shape.BoundBox.XMin-SeperateLinesFromObject/2
        startY= selected.Shape.BoundBox.YMin-SeperateLinesFromObject/2
        startZ= selected.Shape.BoundBox.ZMin

        Xvectors: List[App.Vector] = []
        Yvectors: List[App.Vector] = []
        Zvectors: List[App.Vector] = []


        Xvectors.append(App.Vector(NewX,startY,0))
        Xvectors.append(App.Vector(NewX,NewY,0))

        Yvectors.append(App.Vector(startX,NewY,0))
        Yvectors.append(App.Vector(NewX,NewY,0))

        Zvectors.append(App.Vector(NewX,NewY,startZ))
        Zvectors.append(App.Vector(NewX,NewY,NewZ))
        
        _vectors=[]
        _vectors.append(Xvectors)
        _vectors.append(Yvectors)
        _vectors.append(Zvectors)

        #TODO: I don't know why I should return the length in this order
        leng=[]
        leng.append(lengthY)
        leng.append(lengthX)
        leng.append(lengthZ)
        return (_vectors,leng)

    def getXYZdimOfSelectedObject(self,selected):
        try:    
            (vectors,lengths)=self.returnVectorsFromBoundaryBox(selected)
            #Create the lines
            self.smartInd.clear()
            self.smartInd.append(smartLines(vectors[0],"{0:.2f}".format(lengths[0]),5,self))
            self.smartInd.append(smartLines(vectors[1],"{0:.2f}".format(lengths[1]),5,self))
            self.smartInd.append(smartLines(vectors[2],"{0:.2f}".format(lengths[2]),5,self))
            for i in self.smartInd:
                i.set_target(selected)
            #set selected object to each smartline 
            if self._mywin==None :
                self._mywin=win.Fr_CoinWindow()
            self._mywin.addWidget(self.smartInd)
            self._mywin.show()     

        except Exception as err:
            App.Console.PrintError("'Design456_SmartScale' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def Activated(self):
        try:
            select = Gui.Selection.getSelection()
            if len(select) != 1:
                # Only one object must be selected
                errMessage = "Select one object to scale"
                faced.getInfo().errorDialog(errMessage)
                return
            self.getXYZdimOfSelectedObject(select[0])
            #Create a tab and show it 
            #TODO : I don't know how to give focus to the tab
            mw = self.getMainWindow()
            mw.show()

        # we have a selected object. Try to show the dimensions. 
        except Exception as err:
            App.Console.PrintError("'Design456_SmartScale' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def __del__(self):
        """ 
            class destructor
            Remove all objects from memory even fr_coinwindow
        """
        try:
            for i in self.smartInd:
                i.hide()
                i.__del__()
                del i  # call destructor
            if self._mywin!=None:
                self._mywin.hide()
                del self._mywin
                self._mywin=None
        except Exception as err:
            App.Console.PrintError("'Design456_SmartScale' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)    
    
    def getMainWindow(self):
        try:
            toplevel = QtGui.QApplication.topLevelWidgets()
            self.mw=None
            for i in toplevel:
                if i.metaObject().className() == "Gui::MainWindow":
                    self.mw=i    
            if self.mw==None:
                raise Exception("No main window found")
            dw=self.mw.findChildren(QtGui.QDockWidget)
            for i in dw:
                if str(i.objectName()) == "Combo View":
                    self.tab= i.findChild(QtGui.QTabWidget)
                elif str(i.objectName()) == "Python Console":
                    self.tab= i.findChild(QtGui.QTabWidget)
            if self.tab==None:
                    raise Exception ("No tab widget found")

            self.dialog=QtGui.QDialog()
            oldsize=self.tab.count()
            print("oldsize",oldsize)
            self.tab.addTab(self.dialog,"Smart Scale")
            self.tab.setCurrentWidget(self.dialog)
            self.dialog.resize(200,450)
            self.dialog.setWindowTitle("Smart Scale")
            la = QtGui.QVBoxLayout(self.dialog)
            e1 = QtGui.QLabel("(Smart Scale)\nFor quicker\nresizing any\n3D Objects")
            commentFont=QtGui.QFont("Times",12,True)
            e1.setFont(commentFont)
            la.addWidget(e1)
            okbox = QtGui.QDialogButtonBox(self.dialog)
            okbox.setOrientation(QtCore.Qt.Horizontal)
            okbox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
            la.addWidget(okbox)
            QtCore.QObject.connect(okbox, QtCore.SIGNAL("accepted()"), self.hide)
            QtCore.QObject.connect(okbox, QtCore.SIGNAL("rejected()"), self.hide)
            QtCore.QMetaObject.connectSlotsByName(self.dialog)
            return self.dialog
        except Exception as err:
            App.Console.PrintError("'Design456_SmartScale' Failed. "
                               "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)


    def hide(self):
        self.dialog.hide()
        del self.dialog
        dw=self.mw.findChildren(QtGui.QDockWidget)
        newsize=self.tab.count()
        self.tab.removeTab(newsize-1) # it is 0,1,2,3 ..etc    
        self.__del__()  # Remove all smart scale 3dCOIN widgets

    def GetResources(self):
        return {
            'Pixmap': Design456Init.ICON_PATH +'smartscale.svg',
            'MenuText': 'SmartScale',
                        'ToolTip':  'Smart Scale'
        }

Gui.addCommand('Design456_SmartScale', Design456_SmartScale())






class Design456_DirectScale:
    """
    Direct scaling of any 3D Object by draging either uniform arrow or
    un-uniform arrows.
    
    """
    mw=None
    dialog=None
    tab=None
    smartInd=[]
    _mywin=None
    
    def returnVectorsFromBoundaryBox(self,selected):
        try:
            #Max object length in all directions        
            lengthX =selected.Shape.BoundBox.XLength
            lengthY =selected.Shape.BoundBox.YLength
            lengthZ =selected.Shape.BoundBox.ZLength

            #Make the start 2 mm before the object is placed
            startX= selected.Shape.BoundBox.XMax+SeperateLinesFromObject/2
            startY= selected.Shape.BoundBox.YMax+SeperateLinesFromObject/2
            startZ= selected.Shape.BoundBox.ZMax+SeperateLinesFromObject/2

            p1: App.Vector=None
            p2: App.Vector=None
            _vectors: List[App.Vector] = []

            leng=[]
            leng.append(lengthX)
            leng.append(lengthY)
            leng.append(lengthZ)

            p1=App.Vector(startX,startY,startZ)
            p2=App.Vector(startX+20,startY+20,startZ)
            _vectors.append(p1)
            _vectors.append(p2)
            return (_vectors,leng)
        # we have a selected object. Try to show the dimensions. 
        except Exception as err:
            App.Console.PrintError("'Design456_DirectScale' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
                
    def Activated(self):
        try:
            sel = Gui.Selection.getSelection()
            if len(sel) != 1:
                # Only one object must be selected
                errMessage = "Select one object to scale"
                faced.getInfo().errorDialog(errMessage)
                return 
            (self.mw,self.dialog, self.tab)=faced.createActionTab("Direct Scale").Activated()
            la = QtGui.QVBoxLayout(self.dialog)
            e1 = QtGui.QLabel("(Direct Scale)\nFor quicker\nresizing any\n3D Objects")
            commentFont=QtGui.QFont("Times",12,True)
            self.b1 = QtGui.QPushButton("Uniform")
            self.b1.setCheckable(True)
            self.b1.toggle()
            self.b1.clicked.connect(lambda:self.whichbtn(self.b1))
            self.b1.clicked.connect(self.btnState)
            la.addWidget(self.b1)
            e1.setFont(commentFont)
            la.addWidget(e1)
            okbox = QtGui.QDialogButtonBox(self.dialog)
            okbox.setOrientation(QtCore.Qt.Horizontal)
            okbox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
            la.addWidget(okbox)
            QtCore.QObject.connect(okbox, QtCore.SIGNAL("accepted()"), self.hide)
            QtCore.QObject.connect(okbox, QtCore.SIGNAL("rejected()"), self.hide)
            QtCore.QMetaObject.connectSlotsByName(self.dialog)
            (_vec, length)=self.returnVectorsFromBoundaryBox(sel[0])
            self.smartInd.clear()
            self.smartInd=Fr_Arrow_Widget(_vec,"X-Axis",1)
            self.smartInd.w_color=FR_COLOR.FR_AQUAMARINE
            #self.smartInd.append(Fr_Arrow_Widget(_vec))
            
            #set selected object to each smarArrow 
            if self._mywin==None :
                self._mywin=win.Fr_CoinWindow()
            self._mywin.addWidget(self.smartInd)
            self._mywin.show()     

        # we have a selected object. Try to show the dimensions. 
        except Exception as err:
            App.Console.PrintError("'Design456_DirectScale' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            

    def hide(self):
        self.dialog.hide()
        del self.dialog
        dw=self.mw.findChildren(QtGui.QDockWidget)
        newsize=self.tab.count()
        self.tab.removeTab(newsize-1) # it is 0,1,2,3 ..etc    
        self.__del__()  # Remove all smart scale 3dCOIN widgets

    def  btnState(self):
        if self.b1.isChecked():
            self.b1.setText("Uniform")
            print ("button pressed")
        else:
            self.b1.setText("None Uniform")
            print ("button released")
            
    def whichbtn(self,b):
          print ("clicked button is "+b.text())
    
    def __del__(self):
        try:
            if type(self.smartInd)==list:
                for i in self.smartInd:
                    i.hide()
                    i.__del__()
                    del i  # call destructor
            else:
                self.smartInd.hide()
                self.smartInd.__del__()
                del self.smartInd
                
            if self._mywin!=None:
                self._mywin.hide()
                del self._mywin
                self._mywin=None
        except Exception as err:
            App.Console.PrintError("'Design456_SmartScale' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)    
    
    def GetResources(self):
        return {
            'Pixmap': Design456Init.ICON_PATH +'DirectScale.svg',
            'MenuText': 'Direct Scale',
                        'ToolTip':  'Direct Scale'
        }

Gui.addCommand('Design456_DirectScale', Design456_DirectScale())