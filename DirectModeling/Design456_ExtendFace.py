# -*- coding: utf-8 -*-
from __future__ import unicode_literals
#
# ***************************************************************************
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
import Design456Init
from pivy import coin
from typing import List
from PySide import QtGui, QtCore
from PySide.QtCore import QT_TRANSLATE_NOOP
from ThreeDWidgets.fr_three_arrows_widget import Fr_ThreeArrows_Widget
from ThreeDWidgets.fr_three_arrows_widget import userDataObject
from ThreeDWidgets.fr_draw import draw_FaceSet
from ThreeDWidgets.constant import FR_EVENTS
from ThreeDWidgets.constant import FR_COLOR
from ThreeDWidgets.constant import FR_EVENTS
from draftutils.translate import translate  # for translation
import Part as _part
import FACE_D as faced
import math
from Design456Pref import Design456pref_var  #Variable shared between preferences and other tools

# Some get problem with this.. not used but Might be used in the future.
# I might remove it for this tool. But lets leave it for now.

# try:
#     from OCC import Core
#     from OCC.Core import ChFi2d
# except:
#     pass

__updated__ = '2022-10-16 07:51:22'

class Design456_ExtendFace:
    """[Extend the face's position to a new position.
     This will affect the faces share the face.]
     """

    def __init__(self):
        self._Vector = None
        self.mw = None
        self.dialog = None
        self.tab = None
        self.discObj = None
        self.w_rotation = None
        self._mywin = None
        self.b1 = None
        self.TweakLBL = None
        self.RotateLBL = None
        # coin3D
        self.endVector = None
        self.startVector = None
        # Qt
        self.endVectorQT = None
        self.startVectorQT = None

        self.setupRotation = None
        self.savedVertexes = None
        self.counter = None
        self.run_Once = None
        self.tweakLength = None
        self.newObject = None
        self.selectedObj = None
        self.selectedFace = None
        # Original vectors that will be changed by mouse.
        self.oldFaceVertexes = None
        self.newFaceVertexes = None
        self.newFace = None      # Keep new vectors for the moved old face-vectors

        self.view = None  # used for captureing mouse events
        self.newFaces = None
        self.faceDir = None
        self.FirstLocation = None
        self.coinFaces = None
        self.sg = None  # SceneGraph
        self.discObj = None
        self.OriginalFacePlacement = None
        self.StepSize=1

    # Based on the setTolerance from De-featuring WB,
    # but simplified- Thanks for the author
    def setTolerance(self, sel):
        try:
            if hasattr(sel, 'Shape'):
                ns = sel.Shape.copy()
                new_tol = 0.001
                ns.fixTolerance(new_tol)
                sel.ViewObject.Visibility = False
                sl = App.ActiveDocument.addObject("Part::Feature", "Solid")
                sl.Shape = ns
                g = Gui.ActiveDocument.getObject(sel.Name)
                g.ShapeColor = sel.ViewObject.ShapeColor
                g.LineColor = sel.ViewObject.LineColor
                g.PointColor = sel.ViewObject.PointColor
                g.DiffuseColor = sel.ViewObject.DiffuseColor
                g.Transparency = sel.ViewObject.Transparency
                App.ActiveDocument.removeObject(sel.Name)
                sl.Label = 'Extending'
                return sl

        except Exception as err:
            App.Console.PrintError("'sewShape' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    # Based on the sewShape from De-featuring WB,
    # but simplified- Thanks for the author
    def sewShape(self, sel):
        """[Fix issues might be in the created object]

        Args:
            sel ([3D Object]): [Final object that needs repair.
                                Always new object creates as result of sew]
        """
        try:
            if hasattr(sel, 'Shape'):
                sh = sel.Shape.copy()
                sh.sewShape()
                sl = App.ActiveDocument.addObject("Part::Feature", "compSolid")
                sl.Shape = sh

                g = Gui.ActiveDocument.getObject(sl.Name)
                g.ShapeColor = Gui.ActiveDocument.getObject(
                    sel.Name).ShapeColor
                g.LineColor = Gui.ActiveDocument.getObject(sel.Name).LineColor
                g.PointColor = Gui.ActiveDocument.getObject(
                    sel.Name).PointColor
                g.DiffuseColor = Gui.ActiveDocument.getObject(
                    sel.Name).DiffuseColor
                g.Transparency = Gui.ActiveDocument.getObject(
                    sel.Name).Transparency
                App.ActiveDocument.removeObject(sel.Name)
                App.ActiveDocument.recompute()
                return (sl)

        except Exception as err:
            App.Console.PrintError("'sewShape' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def ExtractFace(self):
        """[Extract the face for movement]
        """
        try:
            self.newFace = App.ActiveDocument.addObject(
                "Part::Feature", "eFace")
            sh = self.selectedFace.copy()
            self.newFace.Shape = sh
            s = App.ActiveDocument.getObject(self.newFace.Name)
            self.OriginalFacePlacement = App.Placement()
            self.OriginalFacePlacement.Base= s.Placement.Base
            self.OriginalFacePlacement.Rotation.Angle=s.Placement.Rotation.Angle
            self.OriginalFacePlacement.Rotation.Axis=s.Placement.Rotation.Axis
            
        except Exception as err:
            App.Console.PrintError("'ExtractFace' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            
    def COIN_recreateObject(self):
        try:
            self.sg.removeChild(self.coinFaces)
            for i in range(0, len(self.savedVertexes)):
                for j in range(0, len(self.savedVertexes[i])):
                    for testItem in range(0, len(self.oldFaceVertexes)):
                        if self.savedVertexes[i][j].Point == self.oldFaceVertexes[testItem].Point:
                            self.savedVertexes[i][j] = self.newFaceVertexes[testItem]

            # We have the new vertices
            self.coinFaces.removeAllChildren()
            for i in self.savedVertexes:
                a = []
                for j in i:
                    a.append(j.Point)
                self.coinFaces.addChild(draw_FaceSet(
                    a, [len(a), ], FR_COLOR.FR_LIGHTGRAY))
            self.sg.addChild(self.coinFaces)

        except Exception as err:
            App.Console.PrintError("'COIN_recreateObject Object' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def recreateObject(self):
        # FIXME:
        # Here
        # We try to create a wire-closed to replace the sides we delete.
        # This will be way to complex . with many bugs :(
        try:
            App.ActiveDocument.removeObject(self.newFace.Name)
            _result = []
            _resultFace = []
            _result.clear()
            for faceVert in self.savedVertexes:
                convert = []
                for vert in faceVert:
                    convert.append(vert.Point)
                _NewVertices = convert
                newPolygon = _part.makePolygon(_NewVertices, True)
                convert.clear()
                newFace = _part.makeFilledFace(newPolygon.Edges)
                if newFace.isNull():
                    raise RuntimeError('Failed to create face')
                nFace = App.ActiveDocument.addObject("Part::Feature", "nFace")
                nFace.Shape = newFace
                _result.append(nFace)
                _resultFace.append(newFace)
            self.newFaces = _result

            solidObjShape = _part.Solid(_part.makeShell(_resultFace))
            newObj = App.ActiveDocument.addObject("Part::Feature", "comp")
            newObj.Shape = solidObjShape
            newObj = self.sewShape(newObj)
            newObj = self.setTolerance(newObj)
            solidObjShape = _part.Solid(newObj.Shape)
            final = App.ActiveDocument.addObject("Part::Feature", "Extended")
            final.Shape = solidObjShape
            App.ActiveDocument.removeObject(newObj.Name)
            for face in self.newFaces:
                App.ActiveDocument.removeObject(face.Name)

        except Exception as err:
            App.Console.PrintError("'recreate Object' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def calculateNewVector(self):
        try:
            self.faceDir = faced.getDirectionAxis()  # face direction
            face=self.selectedFace
            yL = face.CenterOfMass
            uv = face.Surface.parameter(yL)
            nv = face.normalAt(uv[0], uv[1])
            self.normalVector = nv
            # Setup calculation.
            if (face.Surface.Rotation is None):
                plr = plDirection = App.Placement()

                # section direction. When the face doesn't have a Rotation
                yL = face.CenterOfMass
                uv = face.Surface.parameter(yL)
                nv = face.normalAt(uv[0], uv[1])
                direction = yL.sub(nv + yL)
                r = App.Rotation(App.Vector(0, 0, 1), direction)
                plDirection.Base = yL
                plDirection.Rotation.Q = r.Q
                plr = plDirection
                rotation = (plr.Rotation.Axis.x,plr.Rotation.Axis.y,plr.Rotation.Axis.z, math.degrees(plr.Rotation.Angle))
            else:
                ang = face.Surface.Axis.getAngle(App.Vector(0, 0, 1))
                rotation = [0, 0, 1, ang]

            d = self.tweakLength

            self.FirstLocation = yL + d * nv  # the 3 arrows-disc

            if self.oldFaceVertexes[0].Point.z > self.selectedObj.Shape.BoundBox.ZMin:
                self.FirstLocation.z = self.selectedObj.Shape.BoundBox.ZMax
            else:
                self.FirstLocation.z = self.selectedObj.Shape.BoundBox.ZMin

            return rotation

        except Exception as err:

            App.Console.PrintError("'Calculate new Vector. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def saveVertexes(self):
        # Save the vertices for the faces.
        try:
            if len(self.savedVertexes) > 0:
                self.savedVertexes.clear()
            for face in self.selectedObj.Shape.Faces:
                newPoint = []
                for v in face.OuterWire.OrderedVertexes:
                    newPoint.append(v)
                self.savedVertexes.append(newPoint)

        except Exception as err:

            App.Console.PrintError("'saveVertexes' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def Activated(self):
        """[ Executes when the tool is used   ]
        """
        import ThreeDWidgets.fr_coinwindow as win
        self.coinFaces = coin.SoSeparator()
        self.w_rotation = [0.0, 0.0, 0.0]  # disc rotation
        self.setupRotation = [0, 0, 0, 0]  # Whole widget rotation
        self._Vector = App.Vector(0.0, 0.0, 0.0)  # disc POSITION
        self.counter = 0
        self.run_Once = False
        self.tweakLength = 0
        self.oldTweakLength = 0
        self.newFaces = []
        self.savedVertexes = [[]]
        self.tweakLength = 0
        self.StepSize= Design456pref_var.MouseStepSize
        try:
            self.view = Gui.ActiveDocument.ActiveView
            self.sg = self.view.getSceneGraph()
            sel = Gui.Selection.getSelectionEx()

            if len(sel) > 2:
                errMessage = "Please select only one face and try again"
                faced.errorDialog(errMessage)
                return
            # Register undo
            App.ActiveDocument.openTransaction(translate("Design456","ExtendFace"))
            self.selectedObj = sel[0].Object
            self.selectedObj.Visibility = False
            if (hasattr(sel[0], "SubObjects")):
                self.selectedFace = sel[0].SubObjects[0]
            else:
                raise Exception("Not implemented")

            if self.selectedFace.ShapeType != 'Face':
                errMessage = "Please select only one face and try again, was: " + \
                    str(self.selectedFace.ShapeType)
                faced.errorDialog(errMessage)
                return

            # Recreate the object in separated shapes.
            self.saveVertexes()

            if(hasattr(self.selectedFace, "Vertexes")):
                #self.oldFaceVertexes = self.selectedFace.OuterWire.OrderedVertexes
                self.oldFaceVertexes = self.selectedFace.Vertexes
            if not hasattr(self.selectedFace, 'Faces'):
                raise Exception("Please select only one face and try again")
            # TODO: FIXME: WHAT SHOULD WE DO WHEN IT IS A CURVED FACE???
            # if not(type(self.selectedFace.Curve) == _part.Line or
            #       type(self.selectedFace.Curve) == _part.BezierCurve):
            #    msg = "Curve Faces are not supported yet"
            #    faced.errorDialog(msg)
            #    self.hide()

            self.setupRotation = self.calculateNewVector()

            self.ExtractFace()
            self.newFaceVertexes = self.newFace.Shape.Vertexes
            App.ActiveDocument.removeObject(self.selectedObj.Name)

            # Undo
            App.ActiveDocument.openTransaction(
                translate("Design456", "ExtendFace"))

            # Decide how the Degree pad be drawn
            self.discObj = Fr_ThreeArrows_Widget([self.FirstLocation, App.Vector(0, 0, 0)],  #
                                                 # label
                                                 [(str(round(self.w_rotation[0], 2)) + "°" +
                                                   str(round(self.w_rotation[1], 2)) + "°" +
                                                   str(round(self.w_rotation[2], 2)) + "°"), ],
                                                 FR_COLOR.FR_WHITE,  # lblcolor
                                                 [FR_COLOR.FR_RED, FR_COLOR.FR_GREEN,
                                                 FR_COLOR.FR_BLUE],  # arrows color
                                                 # rotation of the disc main
                                                 [0, 0, 0, 0],
                                                 self.setupRotation,  # setup rotation
                                                 [30.0, 30.0, 30.0],  # scale
                                                 1,  # type
                                                 0,  # opacity
                                                 10)  # distance between them
            self.discObj.enableDiscs()

            # Different callbacks for each action.
            self.discObj.w_xAxis_cb_ = self.MouseDragging_cb
            self.discObj.w_yAxis_cb_ = self.MouseDragging_cb
            self.discObj.w_zAxis_cb_ = self.MouseDragging_cb

            self.discObj.w_discXAxis_cb_ = self.RotatingFace_cb
            self.discObj.w_discYAxis_cb_ = self.RotatingFace_cb
            self.discObj.w_discZAxis_cb_ = self.RotatingFace_cb

            self.discObj.w_callback_ = self.callback_release
            self.discObj.w_userData.callerObject = self

            self.COIN_recreateObject()

            if self._mywin is None:
                self._mywin = win.Fr_CoinWindow()

            self._mywin.addWidget(self.discObj)
            mw = self.getMainWindow()
            self._mywin.show()

            App.ActiveDocument.recompute()

        except Exception as err:

            App.Console.PrintError("'Activated' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def getMainWindow(self):
        """[Create the tab for the tool]

        Raises:
            Exception: [If no tabs were found]
            Exception: [If something unusual happen]

        Returns:
            [dialog]: [the new dialog which will be added as a tab to the tab section of FreeCAD]
        """
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
            oldsize = self.tab.count()
            self.dialog = QtGui.QDialog()
            self.tab.addTab(self.dialog, "Extend Face")
            self.frmRotation = QtGui.QFrame(self.dialog)
            self.dialog.resize(200, 450)
            self.frmRotation.setGeometry(QtCore.QRect(10, 190, 231, 181))
            self.lblTweakResult = QtGui.QLabel(self.dialog)
            self.lblTweakResult.setGeometry(QtCore.QRect(10, 0, 191, 61))
            font = QtGui.QFont()
            font.setPointSize(10)
            self.lblTweakResult.setFont(font)
            self.lblTweakResult.setObjectName("lblTweakResult")
            btnOK = QtGui.QDialogButtonBox(self.dialog)
            btnOK.setGeometry(QtCore.QRect(175, 175, 111, 61))
            font = QtGui.QFont()
            font.setPointSize(10)
            font.setBold(True)
            font.setWeight(75)
            btnOK.setFont(font)
            btnOK.setObjectName("btnOK")
            btnOK.setStandardButtons(QtGui.QDialogButtonBox.Ok)
            self.lblTitle = QtGui.QLabel(self.dialog)
            self.lblTitle.setGeometry(QtCore.QRect(10, 10, 281, 91))
            font = QtGui.QFont()
            font.setFamily("Times New Roman")
            font.setPointSize(10)
            self.lblTitle.setFont(font)
            self.lblTitle.setObjectName("lblTitle")
            self.TweakLBL = QtGui.QLabel(self.dialog)
            self.TweakLBL.setGeometry(QtCore.QRect(10, 145, 321, 40))
            font = QtGui.QFont()
            font.setPointSize(10)
            font = QtGui.QFont()
            font.setPointSize(10)

            _translate = QtCore.QCoreApplication.translate
            self.dialog.setWindowTitle(_translate(
                "Dialog", "Extend Face"))

            self.lblTitle.setText(_translate("Dialog", "(Extend Face)\n"
                                             "Tweak an object\n Use X, Y, or Z axis to pull/push an"))
            self.TweakLBL.setFont(font)

            self.TweakLBL.setText(_translate("Dialog", "Length = 0.0"))
            QtCore.QObject.connect(
                btnOK, QtCore.SIGNAL("accepted()"), self.hide)
            QtCore.QMetaObject.connectSlotsByName(self.dialog)
            self.tab.setCurrentWidget(self.dialog)
            return self.dialog

        except Exception as err:
            App.Console.PrintError("'Activated' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def RotatingFace_cb(self, userData=None):
        """[Rotation of the face by using the discs.
        This is the callback used for all axis (X,Y and Z)]

        Args:
            userData ([type], optional): [description]. Defaults to None.
        """
        events = userData.events
        if type(events) != int:
            print("event was not int")
            return
        if self.discObj.w_userData.Disc_cb is False:
            if self.discObj.w_userData.Axis_cb is True:
                self.MouseDragging_cb(userData)
                return
            else:
                return  # We cannot allow this tool
        self.oldFaceVertexes = self.newFaceVertexes
        s = App.ActiveDocument.getObject(self.newFace.Name)
        s.Placement = self.OriginalFacePlacement        
        if self.discObj.w_userData.discObj.axisType == 'X':
            faced.RotateObjectToCenterPoint(
                self.newFace, 0, 0, self.discObj.w_userData.discObj.w_discAngle[0])
        elif self.discObj.w_userData.discObj.axisType == 'Y':
            faced.RotateObjectToCenterPoint(
                self.newFace, 0, self.discObj.w_userData.discObj.w_discAngle[1], 0)
        elif self.discObj.w_userData.discObj.axisType == 'Z':
            faced.RotateObjectToCenterPoint(
                self.newFace, self.discObj.w_userData.discObj.w_discAngle[2], 0, 0,)
        self.newFaceVertexes = self.newFace.Shape.Vertexes
        self.COIN_recreateObject()

    def MouseDragging_cb(self, userData=None):
        """[Move face by dragging the face. As far as the mouse is pressed. 
        This is the callback for all X,Y and Z arrows]
        Args:
            userData ([type], optional): [User Data]. Defaults to None.
        """
        try:
            self.StepSize= Design456pref_var.MouseStepSize
            events = userData.events
            if type(events) != int:
                print("event was not int")
                return
            if events != FR_EVENTS.FR_MOUSE_DRAG:
                return #We accept only mouse drag
                    
            if self.discObj.w_userData.Axis_cb is False:
                if self.discObj.w_userData.Disc_cb is True:
                    self.RotatingFace_cb(userData)
                    return
                else:
                    return  # We cannot allow this tool

            self.endVector = App.Vector(self.discObj.w_parent.w_lastEventXYZ.Coin_x,
                                        self.discObj.w_parent.w_lastEventXYZ.Coin_y,
                                        self.discObj.w_parent.w_lastEventXYZ.Coin_z)
            if self.run_Once is False:
                self.run_Once = True
                # only once
                self.startVector = self.endVector
                self.mouseToArrowDiff = self.endVector.sub(self.discObj.w_vector[0])/self.StepSize

            deltaChange=(self.endVector.sub(self.startVector)).dot(self.normalVector)
            self.tweakLength = self.StepSize* (int(deltaChange/self.StepSize))

            if abs(self.oldTweakLength-self.tweakLength) < 1:
                return  # we do nothing
            self.TweakLBL.setText(
                "Length = " + str(round(self.tweakLength, 1)))
            # must be tuple
            self.discObj.label(["Length = " + str(round(self.tweakLength, 1)), ])
            self.discObj.lblRedraw()
            newPos= self.endVector.sub(self.mouseToArrowDiff)
            self.oldFaceVertexes = self.newFaceVertexes
            if self.discObj.w_userData.discObj.axisType == 'X':
                self.newFace.Placement.Base.x = self.StepSize*(int(newPos.x/self.StepSize))
                self.discObj.w_vector[0].x = self.StepSize*(int(newPos.x/self.StepSize))
            elif self.discObj.w_userData.discObj.axisType == 'Y':
                self.newFace.Placement.Base.y = self.StepSize*(int(newPos.y/self.StepSize))
                self.discObj.w_vector[0].y = self.StepSize*(int(newPos.y/self.StepSize))
            elif self.discObj.w_userData.discObj.axisType == 'Z':
                self.newFace.Placement.Base.z = self.StepSize*(int(newPos.z/self.StepSize))
                self.discObj.w_vector[0].z = self.StepSize*(int(newPos.z/self.StepSize))
            else:
                # nothing to do here  #TODO : This shouldn't happen
                return
            self.newFaceVertexes = self.newFace.Shape.Vertexes
            self.COIN_recreateObject()
            self.discObj.redraw()

        except Exception as err:
            App.Console.PrintError("'Activated' Release Filed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            
    def callback_release(self, userData: userDataObject = None):
        try:
            events = userData.events
            print("mouse release")
            self.discObj.remove_focus()
            self.run_Once = False

        except Exception as err:
            App.Console.PrintError("'MouseDragging_cb'  Filed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def smartlbl_callback(self, userData: userDataObject = None):
        print("lbl callback")
        pass

    def callback_Rotate(self, userData: userDataObject = None):

        if (self.RotateLBL is not None):
            self.RotateLBL.setText("Rotation Axis= " + "(" +
                                   str(self.w_rotation[0])+","
                                   + str(self.w_rotation[1]) +
                                   "," +
                                   str(self.w_rotation[2]) + ")"
                                   + "\nRotation Angle= " + str(angle) + " °")

        print("Not impolemented ")

    def hide(self):
        """
        Hide the widgets. Remove also the tab.
        TODO:
        For this tool, I decide to choose "hide" to merge, or leave it "as is" here.
        I can do that during the extrusion (moving the pad), but that will be an action
        without undo. Here the user will be finished with the extrusion and want to leave the tool
        TODO: If there will be a discussion about this, we might change this behavior!!
        """
        App.ActiveDocument.commitTransaction() #undo reg.
        
        self.dialog.hide()
        self.recreateObject()

        # Remove coin objects
        self.coinFaces.removeAllChildren()
        self.sg.removeChild(self.coinFaces)

        del self.dialog
        dw = self.mw.findChildren(QtGui.QDockWidget)
        newsize = self.tab.count()  # Todo : Should we do that?
        self.tab.removeTab(newsize - 1)  # it ==0,1,2,3 .etc

        App.ActiveDocument.commitTransaction()  # undo reg.
        faced.showFirstTab()
        self.__del__()  # Remove all smart Extrude Rotate 3dCOIN widgets

    def __del__(self):
        """
            class destructor
            Remove all objects from memory even fr_coinwindow
        """
        try:
            self.discObj.hide()
            self.discObj.__del__()  # call destructor
            if self._mywin is not None:
                self._mywin.hide()
                del self._mywin
                self._mywin = None
            del self.discObj
            self.mw = None
            self.dialog = None
            self.tab = None
            self._mywin = None
            self.b1 = None
            self.TweakLBL = None
            self.run_Once = None
            self.endVector = None
            self.startVector = None
            self.tweakLength = None

            self.selectedObj = None
            self.direction = None
            self.setupRotation = None
            self.Rotation = None
            self.FirstLocation = None
            del self.selectedObj
            del self.selectedFace
            self.savedVertexes.clear()
            del self.newFaceVertexes
            del self.oldFaceVertexes
            self.coinFaces.removeAllChildren()
            self.sg.removeChild(self.coinFaces)
            del self.coinFaces
            self.coinFaces = None
            del self

        except Exception as err:
            App.Console.PrintError("'Activated' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def GetResources(self):
        return {
            'Pixmap': Design456Init.ICON_PATH + 'Design456_ExtendFace.svg',
            'MenuText': ' Extend Face',
            'ToolTip':  ' Extend Face'
        }


Gui.addCommand('Design456_ExtendFace', Design456_ExtendFace())
