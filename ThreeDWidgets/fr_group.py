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
import pivy.coin as coin
import Design456Init
import Draft as _draft
from ThreeDWidgets import fr_widget
from ThreeDWidgets import constant
from typing import List

# Group class. Use this to collect several widgets.

__updated__ = '2022-11-02 19:52:32'

class Fr_Group(fr_widget.Fr_Widget):
    # Any drawing/Everything should be added to this later
    # This will keep the link to the main window.
    def __init__(self, vectors: List[App.Vector] = [], l: str = ""):
        if vectors is None:
            vectors = []
        super().__init__(vectors, l)

        self.w_widgetType = constant.FR_WidgetType.FR_GROUP
        # Root of the children (coin)
        self.w_mainfrCoinWindow = None
        self.w_mainfrQtWindow = None
        self.w_children = []
        # Initialize them as None.

    def addWidget(self, widgets):
        """[Add new Fr_Widget to the group. Save the main window also]

        Args:
            widgets ([Fr_Widget object]): [Widget to add to the group]
        """
        if type(widgets) == list:
            for widget in widgets:
                widget.w_parent = self.w_mainfrCoinWindow
                self.w_children.append(widget)
        else:
            widgets.w_parent = self.w_mainfrCoinWindow
            self.w_children.append(widgets)

    def removeWidget(self, widgets):
        """
        Remove the widget from the group. This will eliminate
        the widget from getting events.
        """
        try:
            if type(widgets) == list:
                for widget in widgets:
                    self.w_children.remove(widget)
            else:
                self.w_children.remove(widgets)
        except:
            pass  # Just ignore the error #Todo is this correct?

    def draw(self):
        for i in self.w_children:
            i.draw()

    def hide(self):
        for i in self.w_children:
            i.hide()

    def show(self):
        for i in self.w_children:
            i.show()

    def draw_label(self):
        for i in self.w_children:
            i.draw_label()

    def lblRedraw(self):
        for i in self.w_children:
            i.lblRedraw()

    def redraw(self):
        for i in self.w_children:
            i.redraw()
    """     TODO: THIS SHOULD BE DONE IN ANOTHER WAY.
    def deactivate(self):

    #Before deactivating the group, we have to remove all children.
    #Think about, you might have several groups inside the Fr_CoinWindow

        try:
            for widget in self.w_children:
                # Remove objects in the Root_SceneGraph
                self.removeSceneNode(widget.w_wdgsoSwitch)
                self.removeSceneNode(widget.w_widgetSoNodes)
                # Remove the widget itself from the group
                del widget
            del self.w_children
        except Exception:
            pass   # just go out
    """
    # All events distributed by this function. We classify the event to be processed by each widget later.

    '''TODO: This is not totally correct:
       answer all the below questions
      1-focus/unfocused must come here,
      2-widget must be under the mouse to get events, otherwise we should just remove focus & selection
      3-Think about selection /Focus / Unfocused how should they work
      4-Keyboard and the above events?
      5-Since this widgetsystem is not intended to have a lot of widgets, is it ok to send events to all widgets?
      6-Do we need to translate/mask Keyboard events? or it is waste of time?
      
      
      '''

    def handle(self, events):
        """send events to all widgets
        Targeted Widget should return 1 if it uses the event 
        Sometimes there might be several widgets that need to get the event, 
        at that time return the event to achieve that. 
        To find the target widget, you have to 
        calculate find  the clicked object related to the mouse position.
        Widgets shouldn't get the event if they are not targeted.
        """
        for wdg in self.w_children:
            if wdg.w_userData is None:
                App.Console.PrintError("ERROR:Widgets w_userData is NONE!")
                continue #skip this widget
            wdg.w_userData.events=  events  #distribute the events to the widgets
            if (wdg.is_active() and wdg.is_visible() and wdg.w_widgetType != constant.FR_WidgetType.FR_WIDGET):
                results = wdg.handle(events)
                if results == 1:
                    return results

    def __del__(self):
        ''' 
        Class destructor
        Remove all children
        '''
        for i in self.w_children:
            i.__del__()
            del i
        self.redraw()  # We have to update the widgets drawing
