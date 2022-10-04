# -*- coding: utf-8 -*-
"""
Created on Mon Oct  3 11:20:48 2022

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
    
        self.startEuroThread()

        self.cellsTableWidget.setCurrentCell(0,0)
        self.cellsTableWidget.cellChanged.connect(self.cellChanged)
        
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
        #print(tbl.item(0,3).text())
        #tbl.setCurrentItem(tbl.item(0,3))
        
    @QtCore.pyqtSlot()
    def startEuroThread(self):
        self.euroThread = readEuroClass(self.cellConfigs)
        self.euroThread.update.connect(self.cellChange)
        self.euroThread.start()
    
    @QtCore.pyqtSlot()
    def cellChanged(self):
        print("cell changed")
        row = self.cellsTableWidget.currentRow()
        col = self.cellsTableWidget.currentColumn()
        if col<=2:
            pass
        else:
            item = self.cellsTableWidget.currentItem()
            value = item.text()
            euroAddr = self.cellConfigs[row]['EurothermAddr']
            euro = ModbusClient(host = euroAddr, port=502, auto_open=True)
            match col:
                case 3:
                    euro.write_single_register(2, int(float(value)*10.0))
                case 4:
                    euro.write_single_register(1282, int(float(value)*10.0))
            euro.write_single_register(2, int(float(value)*10.0))
            euro.close()
    
    @QtCore.pyqtSlot(int, int, str)
    def cellChange(self, row, col, value):
        item = self.cellsTableWidget.item(row, col)
        item.setText(value)
    
    def closeEvent(self, event):
        print("Closing")
        self.euroThread.requestInterruption()
        self.euroThread.stop()
        event.accept()
        self.close()
        
class readEuroClass(QtCore.QThread):
    update = QtCore.pyqtSignal(int, int, str)
    def __init__(self, cellConfigs):
        super().__init__()
        
        self.cellConfigs = cellConfigs
        #self.cells = cells
        self.euros = []
        for cell in self.cellConfigs:
            euro = {"Material":cell['Material'],
                    "Addr":cell['EurothermAddr'],
                    "Connection":ModbusClient(host=cell['EurothermAddr'], 
                                              port=502, auto_open=True)
                    }
            self.euros.append(euro)
    
    def stop(self):
        self._active = False
    
    def run(self):
        wait = 4
        pv_addr = 289 # temp reading (10*degC)
        sp_addr = 2 # temp setpoint (10*degC)
        wo_addr = 4 #working output power (%)
        wsp_addr = 5 # working setpoint
        rr1_addr = 1282 # ramp rate (degC/min)
        cjc_temp_addr = 215
        MVin_addr = 202
        
        self._active = True
        while self._active:
            for euro in self.euros:
                cellNum0 = self.euros.index(euro)
                temp = euro['Connection'].read_holding_registers(pv_addr,1)[0]/10.0
                setPoint = euro['Connection'].read_holding_registers(sp_addr,1)[0]/10.0
                workingSP = euro['Connection'].read_holding_registers(wsp_addr,1)[0]/10.0
                output = euro['Connection'].read_holding_registers(wo_addr,1)[0]/10.0
                rampRate = euro['Connection'].read_holding_registers(rr1_addr,1)[0]/10.0
                #window.cellsTableWidget.item(cellNum0,1).setText(str(temp))
                self.update.emit(cellNum0, 1, str(temp))
                self.update.emit(cellNum0, 2, str(workingSP))
                self.update.emit(cellNum0, 3, str(setPoint))
                self.update.emit(cellNum0, 4, str(rampRate))
                euro['Connection'].close()
        
    
app = QApplication([])
#make shutter buttons turn green when checked
#app.setStyleSheet("QPushButton:checked {background-color:  green;}")
app.setStyle('Fusion')

window = MainWindow()
window.setWindowTitle('Capping Chamber Control')

#worker = euroWorker()

window.show()
sys.exit(app.exec_())