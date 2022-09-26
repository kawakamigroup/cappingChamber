# -*- coding: utf-8 -*-
"""
Created on Mon Sep 26 13:43:17 2022

@author: asc-kawakamigroup (AJ Bishop)
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
from pyModbusTCP.client import ModbusClient

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
                
        
        self.cellConfigs = []
        self.readConfigFile()

        self.startThread()
        # self.row = self.cellsTableWidget.currentRow()
        # self.col = self.cellsTableWidget.currentColumn()
        # self.value = self.cellsTableWidget.item(self.row, self.col).text()
        #print(row, col, value)
        self.cellsTableWidget.focusInEvent.connect(self.userChange)
        
    def readConfigFile(self):
        tbl = self.cellsTableWidget
        # open and read file
        with open("config.txt") as f:
            lines = f.readlines()
        #empty list and dict
        cells1 = []
        cell = {}
        # get info out of config file and make a dict for each cell
        for line in lines:
            if "Cell" in line:
                cell = {}
            elif "}" in line:
                cells1.append(cell)
            else:
                colon = line.find(":")
                key = line[:colon].strip("\n ")
                item = line[colon+1:].strip("\n ")
                cell.update({key:item})
        # pass list of cells to main variable
        self.cellConfigs = cells1
        #print(self.cellConfigs)
        #print(tbl.horizontalHeaderItem(0).text())
        # iterate through list and assign material names in settings table
        # and change the shutter button names to the material name
        for c in cells1:
            cellNum = cells1.index(c)+1
            btn = self.findChild(QPushButton, f"shutter{cellNum}PushButton")
            btn.setText(c['Material'])
            self.cellsTableWidget.item(cellNum-1,0).setText(c['Material'])
        print(tbl.item(0,3).text())
        tbl.setCurrentItem(tbl.item(0,3))

    
# class userCellsTableChange(QRunnable):
#     change = QtCore.pyqtSignal(int, int, str)
#         row = self.cellsTableWidget.currentRow()
#         col = self.cellsTableWidget.currentColumn()
#         value = self.cellsTableWidget.item(row, col).text()
#         self.connect(self.cellsTableChange)
#         self.emit(row, col, value)
    
    @QtCore.pyqtSlot()
    def userChange(self):
        print("User selection change")
        row = self.cellsTableWidget.currentRow()
        col = self.cellsTableWidget.currentColumn()
        value = self.cellsTableWidget.item(row, col).text()
        print(row, col, value)
        self.UCC = userCellChange(row, col, value, True)
        self.UCC.change.connect(self.cellsTableChange)
    
    @QtCore.pyqtSlot()    
    def startThread(self):
        self.euroReadThread = euroRead(self.cellConfigs)
        self.euroReadThread.change.connect(self.cellsTableChange)
        self.euroReadThread.start()
        
    @QtCore.pyqtSlot(int, int, str, bool)
    def cellsTableChange(self, row, col, value, user):
        if user:
            print("User change")
        item = self.cellsTableWidget.item(row, col)
        item.setText(value)
        srow = str(row+1)
        lcd = self.findChild(QLCDNumber, f"cell{srow}TempLCD")
        tempItem = self.cellsTableWidget.item(row, 1)
        lcd.display(tempItem.text())
        
    @QtCore.pyqtSlot()        
    def closeEvent(self, event):
        print("Closing")
        self.euroReadThread.requestInterruption()
        self.euroReadThread.quit()
        #self.euroReadThread.wait()
        event.accept()
        self.close()

class userCellChange(QWidget):
    change = QtCore.pyqtSignal(int, int, str, bool)
    def __init__(self, row, col, value, user):
        super().__init__()
        self.row = row
        self.col = col
        self.value = value
        print("init user cell change", user)
        if user:
            self.run()
    def run(self):
        print("Running userCellChange", self.value)
        #value = self.value
        try:
            value = float(self.value)
            #euro = euroRead.__init__.euros[self.row]
            #conn = ModbusClient(host=euro['Connection'], port = 502, auto_open=True)
            #conn.write_single_register(289, int(value*10.0))
            #conn.close()
            #self.change.emit(self.row, self.col, self.value)
        except:
            print("Error, must input number")
            
        #self.change.emit(self.row, self.col, self.value)


class euroRead(QtCore.QThread):
    change = QtCore.pyqtSignal(int, int, str, bool)
    
    def __init__(self, cellConfigs):
        super().__init__()
        self.cellConfigs = cellConfigs
        self.euros = []
        for cell in cellConfigs:
            euro = {"Material":cell['Material'],
                    "Addr":cell['EurothermAddr'],
                    "Connection":ModbusClient(host=cell['EurothermAddr'], port=502, auto_open=True)
                    }
            self.euros.append(euro)
    
    def run(self):
        pv_addr = 289 # temp reading (degC)
        sp_addr = 2 # temp setpoint (degC)
        wo_addr = 4 #working output power (%)
        wsp_addr = 5 # working setpoint
        rr1_addr = 1282 # ramp rate (degC/min)
        cjc_temp_addr = 215
        MVin_addr = 202
        while True:
            for euro in self.euros:
                cellNum0 = self.euros.index(euro)
                temp = euro['Connection'].read_holding_registers(pv_addr,1)[0]/10.0
                setPoint = euro['Connection'].read_holding_registers(sp_addr,1)[0]/10.0
                workingSP = euro['Connection'].read_holding_registers(wsp_addr,1)[0]/10.0
                output = euro['Connection'].read_holding_registers(wo_addr,1)[0]/10.0
                rampRate = euro['Connection'].read_holding_registers(rr1_addr,1)[0]/10.0
                #window.cellsTableWidget.item(cellNum0,1).setText(str(temp))
                self.change.emit(cellNum0, 1, str(temp), False)
                self.change.emit(cellNum0, 2, str(workingSP), False)
                self.change.emit(cellNum0, 3, str(setPoint), False)
                self.change.emit(cellNum0, 4, str(rampRate), False)
                euro['Connection'].close()
            time.sleep(2)
        
app = QApplication([])
#make shutter buttons turn green when checked
#app.setStyleSheet("QPushButton:checked {background-color:  green;}")
app.setStyle('Fusion')

window = MainWindow()
window.setWindowTitle('Capping Chamber Control')

#worker = euroWorker()

window.show()
sys.exit(app.exec_())