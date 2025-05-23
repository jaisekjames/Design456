# -*- coding: utf-8 -*-
from __future__ import unicode_literals
#
# **************************************************************************
# *                                                                        *
# * This file is a part of the Open Source Design456 Workbench - FreeCAD.  *
# *                                                                        *
# * Copyright (C) 2025                                                    *
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

import os
import sys
import FreeCAD as App
import FreeCADGui as Gui
from pivy import coin
import FACE_D as faced
from PySide.QtCore import QT_TRANSLATE_NOOP
from typing import List
import Design456Init
from PySide import QtGui, QtCore
from ThreeDWidgets.fr_arrow_widget import Fr_Arrow_Widget
from ThreeDWidgets import fr_arrow_widget
from ThreeDWidgets.constant import FR_EVENTS
from ThreeDWidgets.constant import FR_COLOR
from draftutils.translate import translate  # for translation
import math
from ThreeDWidgets import fr_label_draw
# The ration of delta mouse to mm  #TODO :FIXME : Which value we should choose?
MouseScaleFactor = 1.5
__updated__ = '2022-10-15 18:50:48'

'''
    We have to recreate the object each time we change the radius. 
    This means that the redrawing must be optimized 
'''


def callback_move(userData: fr_arrow_widget.userDataObject = None):
    """[summary]
    Callback for the arrow movement. This will be used to calculate the radius of the chamfer operation.
    Args:
        userData (fr_arrow_widget.userDataObject, optional): [description]. Defaults to None.

    Returns:
        [type]: [description] None.
    """
    try:
        if userData is None:
            return  # Nothing to do here - shouldn't be None

        ArrowObject = userData.ArrowObj  # Arrow object
        events = userData.events
        # Tool uses the arrow object (here is the Chamfer)
        linktocaller = userData.callerObject
        if type(events) != int:
            return

        clickwdgdNode = ArrowObject.w_parent.objectMouseClick_Coin3d(ArrowObject.w_parent.w_lastEventXYZ.pos,
                                                          ArrowObject.w_pick_radius, ArrowObject.w_widgetSoNodes)
        clickwdglblNode = ArrowObject.w_parent.objectMouseClick_Coin3d(ArrowObject.w_parent.w_lastEventXYZ.pos,
                                                            ArrowObject.w_pick_radius, ArrowObject.w_widgetlblSoNodes)
        linktocaller.endVector = App.Vector(ArrowObject.w_parent.w_lastEventXYZ.Coin_x,
                                            ArrowObject.w_parent.w_lastEventXYZ.Coin_y,
                                            ArrowObject.w_parent.w_lastEventXYZ.Coin_z)

        if clickwdgdNode is None and clickwdglblNode is None:
            if linktocaller.run_Once is False:
                print("click move")
                return 0  # nothing to do

        if linktocaller.run_Once is False:
            linktocaller.run_Once = True
            linktocaller.startVector = linktocaller.endVector
            linktocaller.mouseToArrowDiff = linktocaller.endVector.sub(userData.ArrowObj.w_vector[0])

         # Keep the old value only first time when drag start
            linktocaller.startVector = linktocaller.endVector
            if not ArrowObject.has_focus():
                ArrowObject.take_focus()
        
        if events != FR_EVENTS.FR_MOUSE_DRAG:
            return #We accept only mouse drag
                
        if linktocaller.direction == "+x":
            linktocaller.ChamferRadius = (-linktocaller.endVector.x +
                                          linktocaller.startVector.x)/MouseScaleFactor
        elif linktocaller.direction == "-x":
            linktocaller.ChamferRadius = (
                linktocaller.endVector.x-linktocaller.startVector.x)/MouseScaleFactor
        elif linktocaller.direction == "+y":
            linktocaller.ChamferRadius = (-linktocaller.endVector.y +
                                          linktocaller.startVector.y)/MouseScaleFactor
        elif linktocaller.direction == "-y":
            linktocaller.ChamferRadius = (
                linktocaller.endVector.y-linktocaller.startVector.y)/MouseScaleFactor
        elif linktocaller.direction == "+z":
            linktocaller.ChamferRadius = (-linktocaller.endVector.z +
                                          linktocaller.startVector.z)/MouseScaleFactor
        elif linktocaller.direction == "-z":
            linktocaller.ChamferRadius = (
                linktocaller.endVector.z-linktocaller.startVector.z)/MouseScaleFactor
        if linktocaller.ChamferRadius <= 0:
            linktocaller.ChamferRadius = 0.00001
        elif linktocaller.ChamferRadius > 8:
            linktocaller.ChamferRadius = 8

        #print("ChamferRadius", linktocaller.ChamferRadius)
        linktocaller.resizeArrowWidgets(linktocaller.endVector.sub(linktocaller.mouseToArrowDiff))
        ArrowObject.changeLabelstr(
            "Radius = " + str(round(linktocaller.ChamferRadius, 4)))
                
        linktocaller.ChamferLBL.setText(
            "Radius = " + str(round(linktocaller.ChamferRadius, 4)))
        linktocaller.reCreatechamferObject()

    except Exception as err:
        App.Console.PrintError("'MouseMove callback' Failed. "
                               "{err}\n".format(err=str(err)))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


def callback_release(userData: fr_arrow_widget.userDataObject = None):
    """
       Callback after releasing the left mouse button. 
       This callback will finalize the chamfer operation. 
       Deleting the original object will be done when the user press 'OK' button
    """
    if (userData is None):
        print("userData is None")
        raise TypeError

    ArrowObject = userData.ArrowObj
    events = userData.events
    linktocaller = userData.callerObject
    # Avoid activating this part several times,
    if (linktocaller.startVector is None):
        return
    print("mouse release")
    ArrowObject.remove_focus()
    linktocaller.run_Once = False
    linktocaller.endVector = App.Vector(ArrowObject.w_parent.w_lastEventXYZ.Coin_x,
                                        ArrowObject.w_parent.w_lastEventXYZ.Coin_y,
                                        ArrowObject.w_parent.w_lastEventXYZ.Coin_z)
    # Undo
    App.ActiveDocument.openTransaction(translate("Design456", "SmartChamfer"))
    linktocaller.startVector = None
    linktocaller.mouseToArrowDiff = 0.0
    App.ActiveDocument.commitTransaction()  # undo reg.
    linktocaller.selectedObj[0].Object.Visibility = False
    if hasattr(linktocaller.selectedObj[0], 'Object'):
        linktocaller.selectedObj[0].Object.Label = linktocaller.Originalname
    App.ActiveDocument.recompute()
    App.ActiveDocument.commitTransaction()  # undo reg.


class Design456_SmartChamfer:
    """
        Apply chamfer to any 3D object by selecting the object, a Face or one or multiple edges 
        Radius of the chamfer is counted by dragging the arrow towards the negative Z axis.
    """
    def __init__(self):
        self._vector = App.Vector(0.0, 0.0, 0.0)
        self.mw = None
        self.dialog = None
        self.tab = None
        self.smartInd = None
        self._mywin = None
        self.b1 = None
        self.ChamferLBL = None
        self.run_Once = False
        self.endVector = None
        self.startVector = None
        # We will make two object, one for visual effect and the other is the original
        self.selectedObj = []
        # 0 is the original    1 is the fake one (just for interactive effect)
        self.mouseToArrowDiff = 0.0
        self.offset = 0.0
        self.AwayFrom3DObject = 30  # Use this to take away the arrow from the object
        # We cannot have zero. TODO: What value we should use? FIXME:
        self.ChamferRadius = 0.0001
        self.objectType = None  # Either shape, Face or Edge.
        self.Originalname = ''
        self.direction = None
        self.saveFirstPosition = None


    def registerShapeType(self):
        '''
            Find out shape-type and save the name in objectType
        '''
        if len(self.selectedObj[0].SubElementNames) == 0:
            self.objectType = 'Shape'
        elif 'Face' in self.selectedObj[0].SubElementNames[0]:
            self.objectType = 'Face'
        elif 'Edge' in self.selectedObj[0].SubElementNames[0]:
            self.objectType = 'Edge'
        else:
            print("Error")

    def resizeArrowWidgets(self, endVec):
        """
        Reposition the arrows by recalculating the boundary box
        and updating the vectors inside each fr_arrow_widget
        """
        if(self.direction == "+x" or self.direction == "-x"):
            self.smartInd.w_vector[0].x = endVec.x  # Only X should affect the arrow
        elif(self.direction == "+y" or self.direction == "-y"):
            self.smartInd.w_vector[0].y = endVec.y  # Only Y should affect the arrow
        elif(self.direction == "+z" or self.direction == "-z"):
            self.smartInd.w_vector[0].z = endVec.z  # Only Z should affect the arrow
        self.smartInd.redraw()
        return

    def getArrowPosition(self):
        """"
         Find out the vector and rotation of the arrow to be drawn.
        """
        #      For now the arrow will be at the top
        rotation = [0.0, 0.0, 0.0, 0.0]
        self.direction = faced.getDirectionAxis()  # Must be getSelectionEx

        if (self.direction == "+x"):
            rotation = [0.0, -1.0, 0.0, 90.0]
        elif (self.direction == "-x"):
            rotation = [0.0, 1.0, 0.0, 90.0]
        elif (self.direction == "+y"):
            rotation = [1.0, 0.0, 0.0, 90.0]
        elif (self.direction == "-y"):
            rotation = [-1.0, 0.0, 0.0, 90.0]
        elif (self.direction == "+z"):
            rotation = [1.0, 0.0, 0.0, 180.0]
        elif (self.direction == "-z"):
            rotation = [1.0, 0.0, 0.0, 0.0]

        if self.objectType == 'Shape':
            # 'Shape'
            # The whole object is selected
            if (self.direction == "+x" or self.direction == "-x"):
                if(self.direction == "+x"):
                    self._vector.x = self.selectedObj[0].Object.Shape.BoundBox.XMax + \
                        self.AwayFrom3DObject
                else:  # (direction=="-x"):
                    self._vector.x = self.selectedObj[0].Object.Shape.BoundBox.XMax - \
                        self.AwayFrom3DObject

                self._vector.y = self.selectedObj[0].Object.Shape.BoundBox.YMax/2
                self._vector.z = self.selectedObj[0].Object.Shape.BoundBox.ZMax/2

            elif (self.direction == "+y" or self.direction == "-y"):
                if(self.direction == "+y"):
                    self._vector.y = self.selectedObj[0].Object.Shape.BoundBox.YMax + \
                        self.AwayFrom3DObject
                else:  # (direction=="-y"):
                    self._vector.y = self.selectedObj[0].Object.Shape.BoundBox.YMax - \
                        self.AwayFrom3DObject
                self._vector.x = self.selectedObj[0].Object.Shape.BoundBox.XMax/2
                self._vector.z = self.selectedObj[0].Object.Shape.BoundBox.ZMax/2

            elif (self.direction == "+z" or self.direction == "-z"):
                if(self.direction == "+z"):
                    self._vector.z = self.selectedObj[0].Object.Shape.BoundBox.ZMax + \
                        self.AwayFrom3DObject
                else:  # (direction=="-z"):
                    self._vector.z = self.selectedObj[0].Object.Shape.BoundBox.ZMax - \
                        self.AwayFrom3DObject
                    self._vector.x = self.selectedObj[0].Object.Shape.BoundBox.XMax/2
                    self._vector.y = self.selectedObj[0].Object.Shape.BoundBox.YMax/2
            return rotation
        if (len(self.selectedObj)==0):
            print("nothing selected")
            return
        vectors = self.selectedObj[0].SubObjects[0].Vertexes
        if self.objectType == 'Face':
            self._vector.z = vectors[0].Z
            for i in vectors:
                self._vector.x += i.X
                self._vector.y += i.Y
                self._vector.z += i.Z
            self._vector.x = self._vector.x/4
            self._vector.y = self._vector.y/4
            self._vector.z = self._vector.z/4

        elif self.objectType == 'Edge':
            # One edge is selected
            self._vector.z = vectors[0].Z
            for i in vectors:
                self._vector.x += i.X
                self._vector.y += i.Y
                self._vector.z += i.Z
            self._vector.x = self._vector.x/2
            self._vector.y = self._vector.y/2
            self._vector.z = self._vector.z/2

        if self.direction == "+x":
            self._vector.x = self._vector.x+self.AwayFrom3DObject
        elif self.direction == "-x":
            self._vector.x = self._vector.x-self.AwayFrom3DObject
        elif self.direction == "+y":
            self._vector.y = self._vector.y+self.AwayFrom3DObject
        elif self.direction == "-y":
            self._vector.y = self._vector.y-self.AwayFrom3DObject
        elif self.direction == "+z":
            self._vector.z = self._vector.z+self.AwayFrom3DObject
        elif self.direction == "-z":
            self._vector.z = self._vector.z-self.AwayFrom3DObject

        return rotation

    def getEdgesNumbersList(self, names=None):
        """ 
        Find the edges and return it back to the caller function
        """
        result = []
        if names is None:
            return None
        if type(names == list):
            # multiple edges
            for name in names:
                for subname in name:
                    edgeNumbor = int(subname[4:len(subname)])
                result.append(edgeNumbor, self.ChamferRadius,
                              self.ChamferRadius)
        else:
            # only one Edge
            edgeNumbor = int(names[4:len(names)])
            result.append((edgeNumbor, self.ChamferRadius, self.ChamferRadius))
        return result

    def getAllSelectedEdges(self):
        # The format must be (Edges Number, Start-radius, End-radius)
        EdgesToBeChanged = []
        if self.objectType == 'Face':
            EdgesToBeChanged = self.selectedObj[0].SubObjects[0].Edges
        elif self.objectType == 'Edge':
            EdgesToBeChanged = self.selectedObj[0].SubObjects
        elif self.objectType == 'Shape':
            EdgesToBeChanged = self.selectedObj[0].Object.Shape.Edges
        else:
            print("Error couldn't find the shape type", self.objectType)
        return EdgesToBeChanged

    def reCreatechamferObject(self):
        """
            Use this function to recreate the target object after applying the chamfer radius.
        """
        # reCreate the chamfer. We cannot avoid recreating the object from scratch
        # That is how opencascade library works.
        try:
            if len(self.selectedObj) >= 2:
                if hasattr(self.selectedObj[1], 'ObjectName'):
                    App.ActiveDocument.removeObject(
                        self.selectedObj[1].ObjectName)
                elif hasattr(self.selectedObj[1], 'Name'):
                    App.ActiveDocument.removeObject(self.selectedObj[1].Name)
                elif hasattr(self.selectedObj[1].Object, 'Name'):
                    App.ActiveDocument.removeObject(
                        self.selectedObj[1].Object.Name)
                else:
                    print("removing failed")
                self.selectedObj.pop(1)

            # This create only a shape. We have to make it as a Part::Feature
            App.ActiveDocument.recompute()
            _shape = self.selectedObj[0].Object.Shape.makeChamfer(
                self.ChamferRadius, self.ChamferRadius, self.getAllSelectedEdges())
            newObj = App.ActiveDocument.addObject('Part::Feature', "temp")
            newObj.Shape = _shape
            self.selectedObj.append(newObj)
            App.ActiveDocument.recompute()

        except Exception as err:
            App.Console.PrintError("'Design456_SmartChamfer' recreatechamferObject-Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self.__del__()

    def Activated(self):
        import ThreeDWidgets.fr_coinwindow as win
        self.selectedObj.clear()
        sel = Gui.Selection.getSelectionEx()
        if len(sel) == 0:
            # An object must be selected
            errMessage = "Select an object, one face or one edge to chamfer"
            faced.errorDialog(errMessage)
            return

        self.selectedObj.append(sel[0])
        self.Originalname = self.selectedObj[0].Object.Name

        # Find Out shapes type.
        self.registerShapeType()
        o = Gui.ActiveDocument.getObject(self.selectedObj[0].Object.Name)

        # Undo
        App.ActiveDocument.openTransaction(
            translate("Design456", "SmartFillet"))
        o.Transparency = 80
        self.reCreatechamferObject()

        # get rotation
        rotation = self.getArrowPosition()

        self.smartInd = Fr_Arrow_Widget( [self._vector, App.Vector(0.0, 0.0, 0.0)],   # w_vector
             ["Radius: 0.0",], 1,                                                     # Label, linewidth
              FR_COLOR.FR_RED, FR_COLOR.FR_WHITE,                                     # color, lblcolor
              rotation,                                                               # rotation
              [1.0, 1.0, 1.0],                                                        # scale 
              0,                                                                      # type
              0.0)                                                                    # opacity   
        self.smartInd.w_callback_ = callback_release
        self.smartInd.w_move_callback_ = callback_move
        self.smartInd.w_userData.callerObject = self
        self.saveFirstPosition = self._vector
        if self._mywin is None:
            self._mywin = win.Fr_CoinWindow()
        self._mywin.addWidget(self.smartInd)
        mw = self.getMainWindow()
        self._mywin.show()

    def __del__(self):
        """ 
            class destructor
            Remove all objects from memory even fr_coinwindow
        """
        try:
            self.smartInd.hide()
            self.smartInd.__del__()  # call destructor
            if self._mywin is not None:
                self._mywin.hide()
                del self._mywin
                self._mywin = None
            App.ActiveDocument.commitTransaction()  # undo reg.

        except Exception as err:
            App.Console.PrintError("'Design456_SmartChamfer' del-Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

    def getMainWindow(self):
        try:
            toplevel = QtGui.QApplication.topLevelWidgets()
            self.mw = None
            for i in toplevel:
                if i.metaObject().className() == "Gui::MainWindow":
                    self.mw = i
            if self.mw is None:
                raise Exception("No main window found")
            dw = self.mw.findChildren(QtGui.QDockWidget)
            for i in dw:
                if str(i.objectName()) == "Model":
                    self.tab = i.findChild(QtGui.QTabWidget)
                elif str(i.objectName()) == "Python Console":
                    self.tab = i.findChild(QtGui.QTabWidget)
            if self.tab is None:
                raise Exception("No tab widget found")

            self.dialog = QtGui.QDialog()
            oldsize = self.tab.count()
            self.tab.addTab(self.dialog, "Smart Chamfer")
            self.tab.setCurrentWidget(self.dialog)
            self.dialog.resize(200, 450)
            self.dialog.setWindowTitle("Smart Chamfer")
            la = QtGui.QVBoxLayout(self.dialog)
            e1 = QtGui.QLabel("(Smart Chamfer)\nFor quicker\nApplying Chamfer")
            commentFont = QtGui.QFont("Times", 12, True)
            self.ChamferLBL = QtGui.QLabel("Chamfer Radius=")
            e1.setFont(commentFont)
            la.addWidget(e1)
            la.addWidget(self.ChamferLBL)
            okbox = QtGui.QDialogButtonBox(self.dialog)
            okbox.setOrientation(QtCore.Qt.Horizontal)
            okbox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
            la.addWidget(okbox)
            QtCore.QObject.connect(
                okbox, QtCore.SIGNAL("accepted()"), self.hide)

            QtCore.QMetaObject.connectSlotsByName(self.dialog)
            return self.dialog

        except Exception as err:
            App.Console.PrintError("'Design456_Chamfer' getMainWindow-Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def hide(self):
        """
        Hide the widgets. Remove also the tab.
        """
        try:
            self.dialog.hide()
            del self.dialog
            dw = self.mw.findChildren(QtGui.QDockWidget)
            newsize = self.tab.count()  # Todo : Should we do that?
            self.tab.removeTab(newsize-1)  # it ==0,1,2,3 ..etc
            temp = self.selectedObj[0]
            if(self.ChamferRadius <= 0.01):
                # Chamfer != applied. return the original object as it was
                if(len(self.selectedObj) == 2):
                    if hasattr(self.selectedObj[1], "Object"):
                        App.ActiveDocument.removeObject(
                            self.selectedObj[1].Object.Name)
                    else:
                        App.ActiveDocument.removeObject(self.selectedObj[1].Name)
                o = Gui.ActiveDocument.getObject(self.selectedObj[0].Object.Name)
                o.Transparency = 0
                o.Object.Label = self.Originalname
            else:
                self.selectedObj[0] = self.selectedObj[1]
                self.selectedObj.pop(1)
                no = App.ActiveDocument.getObject(self.selectedObj[0].Name)
                no.Label = self.Originalname
                App.ActiveDocument.removeObject(temp.Object.Name)
                self.ChamferRadius = 0.0001

            App.ActiveDocument.recompute()
            self.__del__()  # Remove all smart chamfer 3dCOIN widgets

        except Exception as err:
            App.Console.PrintError("'Design456_Chamfer' hide-Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
    def GetResources(self):
        return {
            'Pixmap': Design456Init.ICON_PATH + 'Design456_Chamfer.svg',
            'MenuText': ' Smart Chamfer',
                        'ToolTip':  ' Smart Chamfer'
        }


Gui.addCommand('Design456_SmartChamfer', Design456_SmartChamfer())
