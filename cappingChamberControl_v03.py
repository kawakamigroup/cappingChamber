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
        # load in the GUI developed in Qt Designer
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
                
        # set empty list that will be filled
        # by the config file. Then read the
        # config file
        self.cellConfigs = []
        self.readConfigFile()
    
        # start the thread that continuously reads
        # values from eurotherms
        self.startEuroThread()

        # set currently selected cell to (0,0) to avoid weird
        # value changes during initialization
        self.cellsTableWidget.setCurrentCell(0,0)
        self.cellsTableWidget.cellChanged.connect(self.cellChanged)
        
    def readConfigFile(self):
        # this function reads a configuration file (stored in
        # directory for now) that contains information about
        # each cell including the material, cell type, min
        # and max temperatures, and the IP addr of the
        # eurotherm controlling the cell. Stores these values
        # in a list of dicts and used later by other functions
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
        # iterate through list and assign material names in settings table
        # and change the shutter button names to the material name
        for c in cells1:
            cellNum = cells1.index(c)+1
            btn = self.findChild(QPushButton, f"shutter{cellNum}PushButton")
            btn.setText(c['Material'])
            self.cellsTableWidget.item(cellNum-1,0).setText(c['Material'])
        
    @QtCore.pyqtSlot()
    def startEuroThread(self):
        # this starts the thread that continually reads
        # values from the eurotherms (with some built-in
        # wait time set by programmer)
        
        # call the class (readEuroClass) that is a QThread 
        # object and pass any variables requested by the 
        # __init__ function of that class (cellConfigs)
        self.euroThread = readEuroClass(self.cellConfigs)
        # connect the pyqtSignal (update, defined in
        # readEuroClass) to a function you want to handle
        # the signal (must be a pyqtSlot with same argument
        # structure, cellChange here)
        self.euroThread.update.connect(self.cellChange)
        # start the thread which will initialize the class
        # and automatically its "run" function
        self.euroThread.start()
    
    @QtCore.pyqtSlot()
    def cellChanged(self):
        # this is called only when a value inside a table
        # cell is changed. If the value read from the eurotherm
        # is the same as the previously read value this
        # function is not called. But it is called everytime
        # the user changes a value inside a cell
        row = self.cellsTableWidget.currentRow()
        col = self.cellsTableWidget.currentColumn()
        item = self.cellsTableWidget.currentItem()
        value = item.text()
        if col<=2:
            # first three columns of table are not editable
            pass
        else:
            # open connection to eurotherm, IP addr is stored
            # inside the cellConfigs list of dictionaries
            euroAddr = self.cellConfigs[row]['EurothermAddr']
            euro = ModbusClient(host = euroAddr, port=502, auto_open=True)
            if col == 3:
                # write set point temperature to euro therm
                # addr for process variable (temp) setpoint
                # is 2
                euro.write_single_register(2, int(float(value)*10.0))
                
            elif col == 4:
                # write values for ramp rate
                # default is zero (no ramp rate)
                # addr=35 is ramp up rate and
                # addr=1667 is ramp down rate
                euro.write_single_register(35, int(float(value)*10.0))
                euro.write_single_register(1667, int(float(value)*10.0))

            elif col == 5:
                # write working ouput percentage to eurotherm
                # not sure if this works or is even possible
                # needs work obviously
                #euro.write_single_register(4, int(float(value)*10.0))
                pass
            # close connection to eurotherm
            euro.close()
    
    @QtCore.pyqtSlot(int, int, str)
    def cellChange(self, row, col, value):
        # this function handles writing values
        # read from the eurotherms into the table
        # it is called every time the eurotherms
        # are read. all arguments are passed from
        # the signal emitted by the readEuroClass
        # the pyqtSlot decoration must include the
        # same argument structure as the pyqtSignal
        # it is connected to
        
        # get item @ (row, col) in table
        item = self.cellsTableWidget.item(row, col)
        # set text of item
        item.setText(value)
        # specifically get current temp (in column 1)
        tempItem = self.cellsTableWidget.item(row, 1)
        temp = tempItem.text()
        srow = str(row+1)
        # set LCD to display current temp
        lcd = self.findChild(QLCDNumber, name=f"cell{srow}TempLCD")
        lcd.display(temp)
    
    def closeEvent(self, event):
        # this is called when the program is closed
        # with the "X" in the top right
        print("Closing")
        # request an interrupt of the readEuroClass
        # thread we created earlier
        self.euroThread.requestInterruption()
        # calls the function inside readEuroClass
        # called "stop" which will set a variable
        # to False and end the while loop inside
        # the run function
        self.euroThread.stop()
        # accept the close event (allow the user
        # to close with the red "X")
        event.accept()
        # end the program and close the window
        self.close()
        
class readEuroClass(QtCore.QThread):
    # this is the class that connects to eurotherms
    # and reads values. It is a QThread object which
    # means it starts the following actions off of
    # the main thread
    
    # this update object is a pyqtSignal which must
    # emit its signal to a pyqtSlot with the same
    # argument structure. This object is connected
    # to the cellChange function within the
    # startEuroThread func. See line 115
    update = QtCore.pyqtSignal(int, int, str)
    
    # initialize the class with self, and any arguments
    # you want passed from the main thread
    def __init__(self, cellConfigs):
        super().__init__()
        self.cellConfigs = cellConfigs
        # create empty list of dicts which will hold
        # eurotherm information including the material,
        # the IP addr, and the Modbus connection object
        self.euros = []
        for cell in self.cellConfigs:
            euro = {"Material":cell['Material'],
                    "Addr":cell['EurothermAddr'],
                    "Connection":ModbusClient(host=cell['EurothermAddr'], 
                                              port=502, auto_open=True)
                    }
            self.euros.append(euro)
    
    def stop(self):
        # this function sets the variable below
        # and in turn ends the while loop defined
        # in the following run func
        self._active = False
    
    def run(self):
        # this function is automatically called when
        # the thread is started
        
        # set wait time in between eurotherm reads
        wait = 3
        
        # these are some addr for useful eurotherm
        # parameters. These were found by searching
        # the manual and configuring eurotherms with
        # iTools program
        pv_addr = 289 # temp reading (10*degC) (technically process variable)
        sp_addr = 2 # temp setpoint (10*degC)
        wo_addr = 4 #working output power (%)
        wsp_addr = 5 # working setpoint
        rrUp_addr = 35 # ramp rate going up(degC/min)
        rrdown_addr = 1667 # ramp rate going down(degC/min)
        cjc_temp_addr = 215
        MVin_addr = 202
        # start while loop
        self._active = True
        while self._active:
            # iterate through eurotherms
            for euro in self.euros:
                # read values
                cellNum0 = self.euros.index(euro)
                temp = euro['Connection'].read_holding_registers(pv_addr,1)[0]/10.0
                setPoint = euro['Connection'].read_holding_registers(sp_addr,1)[0]/10.0
                workingSP = euro['Connection'].read_holding_registers(wsp_addr,1)[0]/10.0
                output = euro['Connection'].read_holding_registers(wo_addr,1)[0]/10.0
                rampRate = euro['Connection'].read_holding_registers(rrUp_addr,1)[0]/10.0
                # send values to main thread via pyqtSlot
                # that was connected to this pyqtSignal
                # previously (see line 115)
                self.update.emit(cellNum0, 1, str(temp))
                self.update.emit(cellNum0, 2, str(workingSP))
                self.update.emit(cellNum0, 3, str(setPoint))
                self.update.emit(cellNum0, 4, str(rampRate))
                self.update.emit(cellNum0, 5, str(output))
                # close the eurotherm connection after readings
                euro['Connection'].close()
            # wait for set amount of time until reading values again
            time.sleep(wait)
    
app = QApplication([])
app.setStyle('Fusion')

window = MainWindow()
window.setWindowTitle('Capping Chamber Control')

window.show()
sys.exit(app.exec_())