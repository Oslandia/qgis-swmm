# -*- coding: UTF-8 -*-

from SwmmAlgorithmProvider import SwmmAlgorithmProvider
from processing.core.Processing import Processing

class Dummy:

    def __init__(self):
        self.provider = SwmmAlgorithmProvider()
    
    def initGui(self):
        Processing.addProvider(self.provider)
    
    def unload(self):
        Processing.removeProvider(self.provider)

def classFactory(iface):
    return Dummy()

