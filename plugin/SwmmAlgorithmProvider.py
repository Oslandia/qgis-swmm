# -*- coding: utf-8 -*-

"""
***************************************************************************
    SwmmAlgorithmProvider.py
    ---------------------
    Date                 : December 2013
    Copyright            : (C) 2013 by Vincent Mora
    Email                : vincent dot mora dot mtl at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Vincent Mora'
__date__ = 'December 2013'
__copyright__ = '(C) 2013, Oslandia'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
from PyQt4.QtGui import *
from processing.core.AlgorithmProvider import AlgorithmProvider
from processing.core.ProcessingConfig import ProcessingConfig, Setting
from processing.core.ProcessingLog import ProcessingLog
from SwmmAlgorithm import SwmmAlgorithm

class SwmmAlgorithmProvider(AlgorithmProvider):

    def __init__(self):
        AlgorithmProvider.__init__(self)
        self.activate = True

    def getDescription(self):
        return 'Swmm (Storm Water Management Model)'

    def getName(self):
        return 'swmm'

    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + '/swmm.png')

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)
        ProcessingConfig.addSetting(Setting(self.getDescription(),
                                    'Swmm_CLI',
                                    'Swmm command line tool',
                                     ''))

    def unload(self):
        print "unloading swmm"
        AlgorithmProvider.unload(self)
        ProcessingConfig.removeSetting('Swmm_CLI')

    def _loadAlgorithms(self):
        print "loading algo"
        try:
            self.algs.append(SwmmAlgorithm())
        except Exception, e:
            ProcessingLog.addToLog(ProcessingLog.LOG_ERROR, 
                'Could not create Swmm algorithm')

