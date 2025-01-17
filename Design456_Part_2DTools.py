# -*- coding: utf-8 -*-
from __future__ import unicode_literals
#
# ***************************************************************************
# *                                                                         *
# *  This file is a part of the Open Source Design456 Workbench - FreeCAD.  *
# *                                                                         *
# *  Copyright (C) 2021                                                     *
# *                                                                         *
# *                                                                         *
# *  This library is free software; you can redistribute it and/or          *
# *  modify it under the terms of the GNU Lesser General Public             *
# *  License as published by the Free Software Foundation; either           *
# *  version 2 of the License, or (at your option) any later version.       *
# *                                                                         *
# *  This library is distributed in the hope that it will be useful,        *
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of         *
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU      *
# *  Lesser General Public License for more details.                        *
# *                                                                         *
# *  You should have received a copy of the GNU Lesser General Public       *
# *  License along with this library; if not, If not, see                   *
# *  <http://www.gnu.org/licenses/>.                                        *
# *                                                                         *
# *  Author : Mariwan Jalal   mariwan.jalal@gmail.com                       *
# ***************************************************************************
import os
import sys
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore  # https://www.freecadweb.org/wiki/PySide
import Draft as _draft
import Part as _part
import Design456Init
import FACE_D as faced
from draftutils.translate import translate  # for translation
from  Design456_Part_3DTools import Design456_SimplifyCompound 

__updated__ = '2022-02-18 21:22:11'


class Design456_CommonFace:
    """[Create a new shape that is the common between two other shapes.]

    """
    def Activated(self):
        App.ActiveDocument.openTransaction(
            translate("Design456", "CommonFace"))
        s=Gui.Selection.getSelectionEx()
        newshape=None
        for obj in s:
            if obj.HasSubObjects:
                sh1=obj.SubObjects[0]
            else:
                sh1=obj.Object.Shape
            if newshape !=None:
                newshape= newshape.common(sh1)
            else:
                newshape= sh1
            App.ActiveDocument.recompute()
        newobj = App.ActiveDocument.addObject("Part::Feature", "CommonFace")
        newobj.Shape=newshape
        App.ActiveDocument.recompute()
        for obj in s:
            App.ActiveDocument.removeObject(obj.Object.Name)
        App.ActiveDocument.recompute()
        App.ActiveDocument.commitTransaction()  # undo reg.de here


    def GetResources(self):
        return{
            'Pixmap':   Design456Init.ICON_PATH + 'CommonFace.svg',
            'MenuText': 'CommonFace',
            'ToolTip':  'CommonFace between 2-2D Faces'
        }


Gui.addCommand('Design456_CommonFace', Design456_CommonFace())


# Subtract faces


class Design456_SubtractFaces:
    def Activated(self):
        App.ActiveDocument.openTransaction(
            translate("Design456", "SubtractFace"))
        s=Gui.Selection.getSelectionEx()
        newshape=None
        for obj in s:
            if obj.HasSubObjects:
                sh1=obj.SubObjects[0]
            else:
                sh1=obj.Object.Shape
            if newshape !=None:
                newshape= newshape.cut(sh1)
            else:
                newshape= sh1
            App.ActiveDocument.recompute()
        newobj = App.ActiveDocument.addObject("Part::Feature", "SubtractFace")
        newobj.Shape=newshape
        App.ActiveDocument.recompute()
        for obj in s:
            App.ActiveDocument.removeObject(obj.Object.Name)
        App.ActiveDocument.recompute()
        App.ActiveDocument.commitTransaction()  # undo reg.de here

    def GetResources(self):
        return{
            'Pixmap':   Design456Init.ICON_PATH + 'SubtractFace.svg',
            'MenuText': 'Subtract Faces',
            'ToolTip':  'Subtract 2-2D Faces'
        }


Gui.addCommand('Design456_SubtractFaces', Design456_SubtractFaces())

# Combine two faces


class Design456_CombineFaces:
    def Activated(self):

        App.ActiveDocument.openTransaction(
            translate("Design456", "CombineFaces"))
        s=Gui.Selection.getSelectionEx()
        newshape=None
        for obj in s:
            if obj.HasSubObjects:
                sh1=obj.SubObjects[0]
            else:
                sh1=obj.Object.Shape
            if newshape !=None:
                newshape= newshape.fuse(sh1)
            else:
                newshape= sh1
            App.ActiveDocument.recompute()
        newobj = App.ActiveDocument.addObject("Part::Feature", "CombineFaces")
        newobj.Shape=newshape
        App.ActiveDocument.recompute()
        for obj in s:
            App.ActiveDocument.removeObject(obj.Object.Name)
        App.ActiveDocument.recompute()
        simp= Design456_SimplifyCompound()
        simp.Activated(newobj)
        App.ActiveDocument.recompute()
        App.ActiveDocument.commitTransaction()  # undo reg.de here

    def GetResources(self):
        return{
            'Pixmap':   Design456Init.ICON_PATH + 'CombineFaces.svg',
            'MenuText': 'Combine Face',
            'ToolTip':  'Combine 2-2D Faces'
        }


Gui.addCommand('Design456_CombineFaces', Design456_CombineFaces())
# Surface between two line


class Design456_Part_Surface:

    def Activated(self):
        try:

            s = Gui.Selection.getSelectionEx()
            if (len(s) < 1 or len(s) > 2):
                # Two object must be selected
                errMessage = "Select two edges or two wire to make a face or "
                faced.errorDialog(errMessage)
                return
            elementsName = None
            subObj = None
            obj1=None
            obj2=None
            if len(s)==1:
                obj1shp= s[0].SubObjects[0].copy()
                obj1=App.ActiveDocument.addObject('Part::Feature',"E1")
                obj1.Shape=obj1shp
                obj2shp= s[0].SubObjects[1].copy()
                obj2=App.ActiveDocument.addObject('Part::Feature',"E2")
                obj2.Shape=obj2shp
                App.ActiveDocument.recompute()
                elementsName=[obj1.Name, obj2.Name]
                subObj = [obj1, obj2]
            elif len(s)==2 :
                obj1shp= s[0].SubObjects[0].copy()
                obj1=App.ActiveDocument.addObject('Part::Feature',"E1")
                obj1.Shape=obj1shp
                obj2shp= s[1].SubObjects[0].copy()               
                obj2=App.ActiveDocument.addObject('Part::Feature',"E2")
                obj2.Shape=obj2shp
                elementsName=[obj1.Name, obj2.Name]
                subObj = [obj1, obj2]
            for ss in s:
                word = ss.FullName
                if(word.find('Vertex') != -1):
                    # Two lines or curves or wires must be selected
                    errMessage = "Select two edges or two wires not Vertex"
                    faced.errorDialog(errMessage)
                    return
            App.ActiveDocument.openTransaction(
                translate("Design456", "Surface"))

            newObj = App.ActiveDocument.addObject(
                'Part::RuledSurface', 'tempSurface')

            newObj.Curve1 = subObj[0]
            newObj.Curve2 = subObj[1]
            App.ActiveDocument.recompute()
            
            # Make a simple copy of the object
            newShape = _part.getShape(
                newObj, '', needSubElement=False, refine=True)
            tempNewObj = App.ActiveDocument.addObject(
                'Part::Feature', 'Surface')
            tempNewObj.Shape = newShape
            App.ActiveDocument.ActiveObject.Label = 'Surface'
            App.ActiveDocument.recompute()
            if tempNewObj.isValid() is False:
                App.ActiveDocument.removeObject(tempNewObj.Name)
                # Shape != OK
                errMessage = "Failed to create the face"
                faced.errorDialog(errMessage)
            else:
                App.ActiveDocument.removeObject(newObj.Name)
                App.ActiveDocument.commitTransaction()  # undo reg.de here
                App.ActiveDocument.recompute()
                if (obj1 is not None and obj2 is not None):
                    App.ActiveDocument.removeObject(obj1.Name)
                    App.ActiveDocument.removeObject(obj2.Name)

        except Exception as err:
            App.Console.PrintError("'Part Surface' Failed. "
                                   "{err}\n".format(err=str(err)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def GetResources(self):
        return {
            'Pixmap': Design456Init.ICON_PATH + 'Part_Surface.svg',
            'MenuText': 'Part_Surface',
            'ToolTip':  'Part Surface'
        }


Gui.addCommand('Design456_Part_Surface', Design456_Part_Surface())


"""Design456 Part 2D Tools"""


class Design456_Part_2DToolsGroup:
    def __init__(self):
        return

    """Gui command for the group of 2D tools."""

    def GetCommands(self):
        """2D Face commands."""
        return ("Design456_Part_Surface",
                "Design456_CombineFaces",
                "Design456_SubtractFaces",
                "Design456_CommonFace",

                )

    def GetResources(self):
        import Design456Init
        from PySide.QtCore import QT_TRANSLATE_NOOP
        """Set icon, menu and tooltip."""
        _tooltip = ("Different Tools for modifying 2D Shapes")
        return {'Pixmap':  Design456Init.ICON_PATH + 'Design456_2DTools.svg',
                'MenuText': QT_TRANSLATE_NOOP("Design456", "2Dtools"),
                'ToolTip': QT_TRANSLATE_NOOP("Design456", _tooltip)}


Gui.addCommand("Design456_Part_2DToolsGroup", Design456_Part_2DToolsGroup())
