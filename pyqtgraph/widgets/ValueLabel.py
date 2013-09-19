# -*- coding: utf-8 -*-
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.ptime import time
from pyqtgraph.python2_3 import asUnicode
import pyqtgraph as pg
from functools import reduce
import numpy as np

__all__ = ['ValueLabel']

class ValueLabel(QtGui.QLabel):
    """
    QLabel specifically for displaying numerical values.
    Extends QLabel adding some extra functionality:

    - displaying units with si prefix
    - built-in exponential averaging 
    """
    
    def __init__(self, parent=None, suffix='', siPrefix=False, averageTime=0,
            formatStr=None, error=False, errorType='avg'):
        """
        ============ ==================================================================================
        Arguments
        suffix       (str or None) The suffix to place after the value
        siPrefix     (bool) Whether to add an SI prefix to the units and display a scaled value
        averageTime  (float) The length of time in seconds to average values. If this value
                     is 0, then no averaging is performed. If this value is negative, the averaging 
                     time is infinite As this value increases the display value will appear to change 
                     more slowly and smoothly.
        formatStr    (str) Optionally, provide a format string to use when displaying text. The text
                     will be generated by calling formatStr.format(value=, avgValue=, suffix=)
                     (see Python documentation on str.format)
                     This option is not compatible with siPrefix
        error        (bool) Whether to display number with uncertainty
        errorType    (str) How error is computed (stdDev, stdErr, avg, max)
        ============ ==================================================================================
        """
        QtGui.QLabel.__init__(self, parent)
        self.values = []
        self.averageTime = averageTime ## no averaging by default
        self.suffix = suffix
        self.siPrefix = siPrefix
        self.errorType=errorType
        self.error=error
        self.setTextFormat(QtCore.Qt.RichText) ## To respect white space alignment
        if formatStr is None:
            if error:
                formatStr = asUnicode('{avgValue:.{precision}g} ± {avgError:.1g} {suffix}')
            else:
                formatStr = '{avgValue:0.2g} {suffix}'
        self.formatStr = formatStr
    
    @QtCore.Slot(int)
    @QtCore.Slot(float)
    @QtCore.Slot(int,int)
    @QtCore.Slot(float,float)
    def setValue(self, value, error=0):
        now = time()
        self.values.append((now, value,error))
        if self.averageTime >= 0:
            cutoff = now - self.averageTime
            while len(self.values) > 0 and self.values[0][0] < cutoff:
                self.values.pop(0)
        self.update()
        
    def setFormatStr(self, text):
        self.formatStr = text
        self.update()
        
    def setAverageTime(self, t):
        self.averageTime = t

    def setError(self, err):
        self._error=err
        self.update()

    @QtCore.Property(bool)
    def error(self):
        return self._error

    @error.setter
    def error(self,value):
        self.setError(value)

    def setErrorType(self, type):
        self.errorType=type

    @QtCore.Property('QString')
    def errorType(self):
        return self._errorType

    @errorType.setter
    def errorType(self,value):
        self._errorType=value
        
    def averageValue(self):
        return reduce(lambda a,b: a+b, [v[1] for v in self.values]) / float(len(self.values))
        
    def averageError(self):
        if self.errorType=='max':
            err=[v[2] for v in self.values]
            return np.max(err)
        elif self.errorType=='stdDev':
            val=[v[1] for v in self.values]
            return np.std(val)
        elif self.errorType=='stdErr':
            val=[v[1] for v in self.values]
            return np.std(val)/np.sqrt(len(val))
        else:
            err=[v[2] for v in self.values]
            return np.mean(err)

    def paintEvent(self, ev):
        self.setText(self.generateText())
        return QtGui.QLabel.paintEvent(self, ev)
        
    def generateText(self):
        if len(self.values) == 0:
            return ''
        avg = self.averageValue()
        val = self.values[-1][1]
        if self.error:
            avg_err = self.averageError()
            err = self.values[-1][2]
            if self.siPrefix:
                return pg.siFormat(avg,suffix=self.suffix,error=avg_err,
                        groupedError=True,precision=6,space=False).replace(' ',
                                '&nbsp;')
            else:
                if avg == 0 or avg_err == 0:
                    prec = 2
                else:
                    prec = np.floor(np.log10(avg)) - np.floor(np.log10(avg_err)) + 1
                return self.formatStr.format(value=val,avgValue=avg, 
                        suffix=self.suffix,error=err,
                        avgError=avg_err,precision=int(prec)).strip(' ')
        else:
            if self.siPrefix:
                return pg.siFormat(avg, suffix=self.suffix)
            else:
                ##remove space if no suffix
                return self.formatStr.format(value=val, avgValue=avg,
                        suffix=self.suffix).strip(' ')
