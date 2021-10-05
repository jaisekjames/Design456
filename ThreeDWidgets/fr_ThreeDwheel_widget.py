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

import os, sys
import FreeCAD as App
import FreeCADGui as Gui
import ThreeDWidgets
import pivy.coin as coin
from ThreeDWidgets import fr_draw
from ThreeDWidgets import fr_widget
from ThreeDWidgets import constant
from ThreeDWidgets import fr_coin3d
from typing import List
from ThreeDWidgets import fr_label_draw
from ThreeDWidgets.constant import FR_ALIGN
from ThreeDWidgets.constant import FR_EVENTS
from ThreeDWidgets.constant import FR_COLOR
from dataclasses import dataclass
import fr_draw_wheel 

"""
Example how to use this widget. 

                 # show the window and it's widgets. 

"""


@dataclass
class userDataObject:

    def __init__(self):
        self.wheelObj = None  # the wheel widget object
        self.events = None  # events - save handle events here 
        self.callerObject = None  # Class uses the fr_wheel_widget


def callback(userData:userDataObject=None):
    """
            This function will run the when the wheel is clicked 
            event callback. 
    """
    # Subclass this and impalement the callback or just change the callback function
    print("dummy wheel-widget callback")


class Fr_DegreeWheel_Widget(fr_widget.Fr_Widget):

    """
    This class is for drawing a 3D Degrees wheel
    """

    def __init__(self, vectors: List[App.Vector]=[],

                 label: str="", lineWidth=1,
                 _color=FR_COLOR.FR_BLACK,
                 _rotation=[(0.0, 0.0, 1.0), 0.0],
                 _wheelType=0):  

        super().__init__(vectors, label)
        
        self.w_lineWidth = lineWidth  # Default line width
        self.w_widgetType = constant.FR_WidgetType.FR_WHEEL
        
        self.w_callback_ = callback  # External function
        self.w_lbl_calback_ = callback        
        self.w_KB_callback_ = callback        
        self.w_move_callback_ = callback      
        #**************************************************************************
        # We have to define the three wheels here :                               *
        #     ZX  is the first  one -- It has Front Camera View   =0 in the list  *
        #     ZY  is the second one -- It has Right Camera View   =1 in the list  *
        #     XY  is the Third  one -- It has the Top Camera View =2 in the list  *
        #**************************************************************************

        self.w_xAxis_cb : List [callback]
        self.w_yAxis_cb : List [callback]
        self.w_zAxis_cb : List [callback]
        
        self.w_45Axis_cb : List [callback]
        self.w_135Axis_cb : List [callback]
        self.w_wheel_cb : List [callback]

        self.w_wdgsoSwitch = coin.SoSwitch()                       # the whole widget 
        self.w_XsoSeparator:List [coin.SoSeparator]                #For each axis we have 3 of them (Roll=X θ - , Pitch= Y Φ, Yaw = Z ψ )
        self.w_YsoSeparator = List [coin.SoSeparator]              #For each axis we have 3 of them
        self.w_45soSeparator = List [coin.SoSeparator]             #For each axis we have 3 of them
        self.w_135soSeparator = List [coin.SoSeparator]            #For each axis we have 3 of them
        self.w_centersoSeparator = List[coin.SoSeparator]          #For each axis we have 3 of them
                
        self.w_color = _color                                       # TODO: Not sure if we use this
                         
        self.w_Xrotation = [0, 0, 0, 0]           
        self.w_Yrotation = [0, 0, 0, 0]
        self.w_Zrotation = [0, 0, 0, 0]

        
        self.w_userData = userDataObject()  # Keep info about the widget
        # self.w_userData.wheelObj=self
        # self.w_userData.color=_color
        self.releaseDrag = False  # Used to avoid running drag code while it is in drag mode
    def calculateNewRotationDeg(self,vec1:App.Vector=App.Vector(0,0,0) ,
                                vec2:App.Vector=App.Vector(0,0,0)):
        """
        [Calculate the new rotation degree of the whole object after a mouse drag]
        """
        
    def lineWidth(self, width):
        """ Set the line width"""
        self.w_lineWidth = width

    def handle(self, event):
        """
        This function is responsbile of taking events and processing 
        the actions required. If the object != targeted, 
        the function will skip the events. But if the widget was
        targeted, it returns 1. Returning 1 means that the widget
        processed the event and no other widgets needs to get the 
        event. Window object is responsible for distributing the events.
        """
        
        self.w_userData.events = event  # Keep the event always here 
        if type(event) == int:
            if event == FR_EVENTS.FR_NO_EVENT:
                return 1  # we treat this event. Nonthing to do 
        
        clickwdgdNode = fr_coin3d.objectMouseClick_Coin3d(self.w_parent.link_to_root_handle.w_lastEventXYZ.pos,
                                                          self.w_pick_radius, self.w_widgetSoNodes)
        clickwdglblNode = fr_coin3d.objectMouseClick_Coin3d(self.w_parent.link_to_root_handle.w_lastEventXYZ.pos,
                                                           self.w_pick_radius, self.w_widgetlblSoNodes) 
        
        if self.w_parent.link_to_root_handle.w_lastEvent == FR_EVENTS.FR_MOUSE_LEFT_DOUBLECLICK:
            # Double click event.
            if clickwdglblNode != None:
                print("Double click detected")
                # if not self.has_focus():
                #    self.take_focus()
                self.do_lblcallback()
                return 1

        elif self.w_parent.link_to_root_handle.w_lastEvent == FR_EVENTS.FR_MOUSE_LEFT_RELEASE:
            if self.releaseDrag == True:
                self.releaseDrag == False
                print("Release Mouse happened")
                self.do_callback()  # Release callback should be activated even if the wheel != under the mouse 
                return 1
            
            if (clickwdgdNode != None) or (clickwdglblNode != None):
                if not self.has_focus():
                    self.take_focus()
                self.do_callback()
                return 1            
            else:
                self.remove_focus()
                return 0
        
        if self.w_parent.link_to_root_handle.w_lastEvent == FR_EVENTS.FR_MOUSE_DRAG:
            if self.releaseDrag == False:
                if (clickwdgdNode != None) or (clickwdglblNode != None):
                    self.releaseDrag = True   
                    self.take_focus()
                    self.do_move_callback()  # We use the same callback, 
                                      # but user must tell the callback what was
                                      # the event. TODO: Do we want to change this?
                    return 1
            else:
                self.do_move_callback()  # Continue run the callback as far as it != releaseDrag=True
                return 1
        # Don't care events, return the event to other widgets    
        return 0  # We couldn't use the event .. so return 0 

    def draw(self):
        """
        Main draw function. It is responsible to create the node,
        and draw the wheel on the screen. It creates a node for 
        the wheel.
        """
        try:
            pass
            











        except Exception as err:
            App.Console.PrintError("'draw Fr_wheel_Widget' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def draw_label(self, usedColor):
        self.w_lbluserData.linewidth = self.w_lineWidth
        self.w_lbluserData.labelcolor = usedColor
        self.w_lbluserData.vectors = self.w_vector
        self.w_lbluserData.alignment = FR_ALIGN.FR_ALIGN_LEFT_BOTTOM
        lbl = fr_label_draw.draw_label(self.w_label, LabelData)
        self.w_widgetlblSoNodes = lbl
        return lbl

    def move(self, newVecPos):
        """
        Move the object to the new location referenced by the 
        left-top corner of the object. Or the start of the wheel
        if it is an wheel.
        """
        self.resize([newVecPos[0], newVecPos[1]])
        
    @property
    def getVertexStart(self):
        """Return the vertex of the start point"""
        return App.Vertex(self.w_vector[0])

    @property
    def getVertexEnd(self):
        """Return the vertex of the end point"""
        return App.Vertex(self.w_vector[1])

    def show(self):
        self.w_visible = 1
        self.w_wdgsoSwitch.whichChild = coin.SO_SWITCH_ALL  # Show all children

    def redraw(self):
        """
        After the widgets damages, this function should be called.        
        """
        if self.is_visible():
            # Remove the SoSwitch from fr_coinwindo
            self.w_parent.removeSoSwitchFromSceneGraph(self.w_wdgsoSwitch)

            # Remove the node from the switch as a child
            self.removeSoNodeFromSoSwitch()
           
            # Remove the sceneNodes from the widget
            self.removeSoNodes()
            # Redraw label
            
            self.lblRedraw()
            self.draw()
    
    def lblRedraw(self):
        if(self.w_widgetlblSoNodes != None):
            self.w_widgetlblSoNodes.removeAllChildren()
        
    def take_focus(self):
        """
        Set focus to the widget. Which should redraw it also.
        """
        if self.w_hasFocus == 1:
            return  # nothing to do here
        self.w_hasFocus = 1
        self.redraw()

    def activate(self):
        if self.w_active:
            return  # nothing to do
        self.w_active = 1
        self.redraw()

    def deactivate(self):
        """
        Deactivate the widget. which causes that no handle comes to the widget
        """
        if self.w_active == 0:
            return  # Nothing to do
        self.w_active = 0
    
    def __del__(self):
        """
        Class Destructor. 
        This will remove the widget totally. 
        """  
        self.hide()
        try:
            if self.w_parent != None:
                self.w_parent.removeWidget(self)  # Parent should be the windows widget.

            if self.w_parent is not None:
                self.w_parent.removeSoSwitchFromSceneGraph(self.w_wdgsoSwitch)

            self.removeSoNodeFromSoSwitch()
            self.removeSoNodes()
            self.removeSoSwitch()    
                 
        except Exception as err:
            App.Console.PrintError("'del Fr_wheel_Widget' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def hide(self):
        if self.w_visible == 0:
            return  # nothing to do
        self.w_visible = 0
        self.w_wdgsoSwitch.whichChild = coin.SO_SWITCH_NONE  # hide all children
        self.redraw()

    def remove_focus(self):
        """
        Remove the focus from the widget. 
        This happens by clicking anything 
        else than the widget itself
        """
        if self.w_hasFocus == 0:
            return  # nothing to do
        else:
            self.w_hasFocus = 0
            self.redraw()

    def resize(self, vectors: List[App.Vector]):  # Width, height, thickness
        """Resize the widget by using the new vectors"""
        self.w_vector = vectors
        self.redraw()

    def size(self, vectors: List[App.Vector]):
        """Resize the widget by using the new vectors"""
        self.resize(vectors)

    def label_move(self, newPos):
        pass

    def setRotationAngle(self, axis_angle):
        ''' 
        Set the rotation axis and the angle for the whole widget.
        Axis is coin.SbVec3f((x,y,z)
        angle=float number
        '''
        self.w_rotation = axis_angle    #this rotation is for the whole widget (not only the disk)