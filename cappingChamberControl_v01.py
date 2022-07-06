# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 12:59:16 2022

@author: abish
"""

import sys
import os
#import cv2
import io
import math

#import ctypes as C
#import tisgrabber as IC
import numpy as np
import PIL
from PIL import Image  # Python Image Library
Image.MAX_IMAGE_PIXELS = None
import time

from PyQt5 import QtCore, QtGui, QtWidgets, uic                     # uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt, QTimer, QRunnable, QThreadPool, pyqtSlot

from functools import partial
#import pyqtgraph as pg

from datetime import date 
#from scanf import scanf

#import pygame

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("UserInterface/cappingChamberUI_v02.ui",self)
        
        self.threadpool = QThreadPool()
        print(
            "Multithreading with maximum %d threads" % self.threadpool.maxThreadCount()
        )
        
        today = date.today()
        datestr = today.strftime("%Y-%m-%d")
        monthstr = today.strftime("%m")
        yearstr = today.strftime("%Y")

        print(
            f"Date strings, datestr:{datestr}, monthstr:{monthstr}, yearstr:{yearstr}"
            )

        #Connect to shutter control box
        #self.shutterBoxConnection.clicked.connect(self.boxConnect_function)

        #connect shutter buttons to a function
        for i in range(1,5):
            print(i)
            name = i
            btn = self.findChild(QPushButton, f"shutter{name}PushButton")
            btn.clicked.connect(partial(self.shutter_function, name))
        
        #self.shutter1PushButton.clicked.connect(partial(self.shutter_function, "1"))
        #self.shutter2PushButton.clicked.connect(partial(self.shutter_function, "2"))
        #self.shutter3PushButton.clicked.connect(partial(self.shutter_function, "3"))
        #self.shutter4PushButton.clicked.connect(partial(self.shutter_function, "4"))
        
        self.cellsTableWidget.cellChanged.connect(self.cellTableChange_function)
        
        self.cells = []
        self.initCellTable()
        #self.initRecipeCommandList()
        
        self.addStepPushButton.clicked.connect(self.addRecipeStep_function)
        self.recipe = []
        #self.recipeTableWidget.itemSelectionChanged.connect(self.showRecipeDetails)
        self.removeStepPushButton.clicked.connect(self.removeStepWarn)
        
        @QtCore.pyqtSlot()        
        def exitfunction(self):
            self.close()
   
    #@QtCore.pyqtSlot() this decoration prevents checked state (boolean)
                        #from being passed to function
                        #not sure why
    def initCellTable(self):
        # initialize table values
        # all int set as -1 in ui file
        # need to get readings from eurotherms
        # materials set as "Cell#"
        # read config file to get materials and cell type and temp limits?
        rt = 20
        ramp = 25
        
        with open("config.txt") as f:
            lines = f.readlines()
        cells1 = []
        cell = {}
        columns = []
        colNum = self.cellsTableWidget.columnCount()
        
        for c in range(colNum):
            columns.append(self.cellsTableWidget.horizontalHeaderItem(c).text())
        print(columns)
        for line in lines:
            item = ""
            if "Cell" in line:
                cell = {}   
            elif "}" in line:
                cells1.append(cell)    
            
            for col in columns:
                if col in line:
                    find = line.find(":")
                    item = line[find+1:].strip("\n ")
                    print("found", col, item)
                    cell.update({col:item})
                    print(cell)
                elif col != "Material":
                    item = rt
                    cell.update({col:item})
        #print(cells)
        self.cells = cells1
        for c in cells1:
            #print(cells.index(c))
            for col in columns:    
                self.cellsTableWidget.item(cells1.index(c), columns.index(col)).setText(str(c[col]))
            name = cells1.index(c)+1
            btn = self.findChild(QPushButton, f"shutter{name}PushButton")
            btn.setText(c["Material"])
        #print(self.cellsTableWidget.horizontalHeaderItem(2).text())
        
    def initRecipeCommandList(self):
        with open("commands.txt") as f:
            lines = f.readlines()
        cmds = []
        listWidget = self.findChild(QListWidget, "recipeCommandsListWidget")
        for line in lines:
            cmds.append(line.strip("\n "))
            item = QListWidgetItem(line.strip("\n "))
            listWidget.addItem(item)
        print(cmds)

    def boxConnect_function(self):
        self.statusbar.showMessage("Connecting to control box...")
        print("Connecting to control box...")
        
    #@QtCore.pyqtSlot() this decoration prevents checked state (boolean)
                        #from being passed to function
                        #not sure why        
    def shutter_function(self, name, checked):
        state = "closed"
        messageState = state
        color = "firebrick"
        if checked:
            state = "open"
            messageState = "opened"
            color = "limegreen"
        btn = self.findChild(QPushButton, f"shutter{name}PushButton")
        btn.setStyleSheet(f"background-color:{color};")
        m = btn.text()
        print(f"{m} shutter {state}")
        label = self.findChild(QLabel, f"shutter{name}Label")
        label.setText(state)
        self.statusbar.showMessage(f"Shutter {name} {messageState}")
        
    def cellTableChange_function(self, row, col):
        table = self.cellsTableWidget
        value = table.item(row, col).text()
        head = table.horizontalHeaderItem(col).text()
        print(f"Cell change, {row}, {col}, {value}")
        
        if col > 0:
            try:
                value = int(value)
                if value > 0:
                    self.cells[row][head] = value
                    self.cellsTableWidget.item(row, col).setText(str(self.cells[row][head]))
                else:
                    self.cellsTableWidget.item(row, col).setText(str(self.cells[row][head]))
                    print(f"ERROR {head} must be positive int")
            except:
                self.cellsTableWidget.item(row, col).setText(str(self.cells[row][head]))
                print(f"ERROR: {head} must be positive int")
        srow = str(row+1)
        #print(f"cell{srow}TempLCD")
        lcd = self.findChild(QLCDNumber, f"cell{srow}TempLCD")
        lcd.display(table.item(row, 1).text())
        
    def addRecipeStep_function(self):
        #listWidget = self.findChild(QListWidget, "recipeCommandsListWidget")
        #item = listWidget.currentItem()
        #cmd = item.text()
        #print(cmd)
        #if (cmd == "open") or (cmd == "close"):
        self.startPopUpWindow()
        #print("Back to main")
            
            
    @QtCore.pyqtSlot()
    def startPopUpWindow(self):
        self.Window = popUpWindow()                             
        self.Window.setWindowTitle("Add recipe step") #main window title 
        #self.Window.
        #self.Window.ToolsBTN.clicked.connect(self.goWindow1)

        #self.hide() #this will hide the main window
        self.Window.show()

    def showRecipeDetails(self):
        recipe = self.recipe
        #print(recipe, "Called Details Func")
        #rTable = self.findChild(QTableWidget, "recipeTableWidget")
        #sel = rTable.currentRow()
        if len(recipe) > 0:
            print("written recipe")
            rTable = self.findChild(QTableWidget, "recipeTableWidget")
            sel = rTable.currentRow()
            
        else:
            print("No recipe")
            return
        cellCmds = recipe[sel]
        dTable = self.findChild(QTableWidget, "stepDetailsTableWidget")
        #dTable.clear()
        #dTable.setRowCount(0)
        #ks = list(cellCmds[0].keys())
        heads = []
        for c in cellCmds:
            ks = list(c.keys())
            for k in ks[1:]:
                heads.append(str(c[ks[0]]+k))
        #print(heads)
        #heads = list(cellCmds[0].keys()) # must cast keys as list.
        dTable.setColumnCount(len(heads))
        dTable.setHorizontalHeaderLabels(heads) # .keys() gives view of a list not an actual list
        dTable.setRowCount(len(recipe))
        for s in range(len(recipe)): # can't iterate through recipe list directly
            #print("step", s)        # because if a step repeats the details list
            for c in recipe[s]:     # will not fill in correctly
                ks = list(c.keys())
                cell = c[ks[0]]
                for h in ks[1:]:
                    col = heads.index(cell+h)
                    item = QTableWidgetItem(str(c[f"{h}"]))
                    dTable.setItem(s, col, item)
            
    def removeStepWarn(self):
        self.Window = removeStepWarn()
        self.Window.setWindowTitle("Confirm recipe step removal")
        self.Window.show()
    
    def removeRecipeStep_function(self):
        #TODO Add "are you sure" popup window
        recipe = self.recipe
        rTable = self.findChild(QTableWidget, "recipeTableWidget")
        sel = rTable.currentRow()
        old = []
        for r in range(rTable.rowCount()):
            d = {"Name":rTable.item(r,0).text(),
                 "Time":rTable.item(r,1).text()}
            old.append(d)
        #print(old)
        recipe.pop(sel)
        old.pop(sel)
        
        #print(recipe)
        rTable.clear()
        rTable.setRowCount(0)
        for s in range(len(recipe)):
            rTable.insertRow(s)
            rTable.setItem(s,0, QTableWidgetItem(old[s]["Name"]))
            rTable.setItem(s,1, QTableWidgetItem(old[s]["Time"]))
        dTable = self.findChild(QTableWidget, "stepDetailsTableWidget")
        dTable.clear()
        dTable.setRowCount(0)
        dTable.setColumnCount(0)
        self.recipe = recipe
        self.showRecipeDetails()
        
        

class popUpWindow(QWidget):
    def __init__   (self, parent=None):
        super(popUpWindow, self).__init__(parent)
        uic.loadUi("UserInterface/recipePopUpUI_v02.ui",self)
        
        self.resize(700, 500)
        self.okayPushButton.clicked.connect(self.closeWindow_function)
        self.cells = window.cells
        
        self.rTable = window.findChild(QTableWidget, "recipeTableWidget")
        self.step = self.rTable.rowCount()
        
        self.initPopUp(self.cells, self.step)
    
    def initPopUp(self, cells, stepNum):
        
        tbl = self.findChild(QTableWidget, "popUpTempTableWidget")
        
        for c in cells:
            i = cells.index(c)
            name = i + 1
            btn = self.findChild(QPushButton, f"shutter{name}PushButton")
            btn.setText(c["Material"])
            tbl.item(i, 0).setText(str(c["Material"]))
        
        if stepNum > 0:
            recipe = window.recipe
            pStep = len(recipe)-1
            cmds = recipe[pStep]
        
    def closeWindow_function(self):
        cellCmds = []
        tbl = self.findChild(QTableWidget, "popUpTempTableWidget")
        for i in range(4):
            cell = {}
            shutter = "closed"
            m = self.cells[i]["Material"]
            num = i+1
            btn = self.findChild(QPushButton, f"shutter{num}PushButton")
            #print(btn)
            if btn.isChecked():
                shutter = "open"
            cell.update({"Material":m})
            cell.update({"Shutter":shutter})
            cell.update({"Temperature":tbl.item(i,1).text()})
            cell.update({"Ramp":tbl.item(i,2).text()})
            cellCmds.append(cell)
        #print(cellCmds)
        # t = ""
        # step = ""
        # i = 0
        # for cmd in shutterCmds:
        #     m = self.cells[i]["Material"]
        #     if cmd:
        #         t = f"open {m}, "
        #     else:
        #         t = f"close {m}, "
        #     step += t
        #     i+=1
        window.statusbar.showMessage(str(cellCmds[0]))
        rTable = window.findChild(QTableWidget, "recipeTableWidget")
        rows = rTable.rowCount()
        rTable.insertRow(rows)
        rTable.setColumnCount(2)
        rTable.setHorizontalHeaderLabels(["Steps", "Time"])
        stepNameItem = self.findChild(QLineEdit, "stepNameLineEdit")
        stepTimeItem = self.findChild(QDoubleSpinBox, "stepTimeDoubleSpinBox")
        stepTimeUnit = self.findChild(QComboBox, "stepTimeUnitComboBox")
        stepName = stepNameItem.text()
        stepTimeSecs = float(stepTimeItem.value())
        #print(type(stepTimeItem.value()), stepTimeItem.value(), stepTimeUnit.currentText())
        #stepTimeSecs = float(0)
        if stepName == "":
            stepName = "Unnamed Step"
        if stepTimeUnit.currentText() == "minutes":
            stepTimeSecs = stepTimeSecs*60
        elif stepTimeUnit.currentText() == "hours":
            stepTimeSecs = stepTimeSecs*3600
        #else:
        #    stepTimeSecs = stepTimeFl
        #print(stepTimeSecs, type(stepTimeSecs))
        rTable.setItem(rows, 0, QTableWidgetItem(stepName))
        rTable.setItem(rows, 1, QTableWidgetItem(str(stepTimeSecs)))
        recipe = window.recipe
        recipe.append(cellCmds)
        window.showRecipeDetails()
        self.hide()

class removeStepWarn(QWidget):
    def __init__   (self, parent=None):
        super(removeStepWarn, self).__init__(parent)
        uic.loadUi("UserInterface/recipeRemoveStepUI_v01.ui",self)
        
        self.resize(400, 236)
        self.removeStepButtonBox.button(QDialogButtonBox.Yes).clicked.connect(self.closeWarnWindowYes)
        self.removeStepButtonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.closeWarnWindowCancel)
        #self.cells = window.cells
        
        #self.rTable = window.findChild(QTableWidget, "recipeTableWidget")
        #self.step = self.rTable.rowCount()
        
        #self.initPopUp(self.cells, self.step)
    def initRemoveStepWarn(self):
        print("removing recipe step")
        
    def closeWarnWindowYes(self):
        window.removeRecipeStep_function()
        self.hide()
    def closeWarnWindowCancel(self):
        self.hide()

        
app = QApplication([])
#make shutter buttons turn green when checked
#app.setStyleSheet("QPushButton:checked {background-color:  green;}")
app.setStyle('Fusion')

window = MainWindow()
window.setWindowTitle('Capping Chamber Control')

window.show()
sys.exit(app.exec_()) 
