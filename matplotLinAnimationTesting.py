# -*- coding: utf-8 -*-
"""
Created on Fri Jul 29 11:07:37 2022

@author: abish
"""

import sys
from PyQt5 import QtCore, QtGui, QtWidgets, uic                     # uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt, QTimer, QRunnable, QThreadPool, pyqtSlot

from functools import partial
#import pyqtgraph as pg

import datetime as dt
from datetime import date 
import numpy as np
from matplotlib.figure import Figure
from matplotlib.animation import TimedAnimation
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import time
from datetime import timedelta
import threading
import matplotlib
matplotlib.use("Qt5Agg")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("UserInterface/eurothermGraphingUI_testing.ui",self)
        
        print("Running")
        self.hLayout = self.findChild(QGridLayout, "gridLayout")
        
        self.n = []
        self.y = []
        
        print(self.n, self.y)
        
        self.fig = Figure()
        self.ax1 = self.fig.add_subplot()
        self.ax1.set_xlabel('time')
        self.ax1.set_ylabel('raw data')
        self.ax1.plot(self.n, self.y)
        
        self.FC = FigureCanvas(self.fig)

        self.hLayout.addWidget(self.FC, *(0,1))
        
        self.tStart = dt.datetime.now()
        
    def animate(self, i, n, y):
        td = dt.datetime.now() - self.tStart
        td = timedelta.total_seconds(td)
        self.n.append(td)
        self.y.append(np.sin(td/3.14))
        print(n[-1], y[-1])
        n = n[-60:]
        y = y[-60:]
        
        #line = self.ax1.
        self.ax1.clear()
        self.ax1.set_xlabel('time')
        self.ax1.set_ylabel('raw data')
        self.ax1.plot(n,y)

    def closeEvent(self, event):
        ani.event_source.stop()
        self.close()

app = QApplication([])
app.setStyle('Fusion')

window = MainWindow()
window.setWindowTitle('Eurotherm Testing')
ani = matplotlib.animation.FuncAnimation(window.fig, window.animate, fargs=(window.n, window.y),interval=500)
window.show()
sys.exit(app.exec_()) 