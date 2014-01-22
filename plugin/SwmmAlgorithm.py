# -*- coding: utf-8 -*-

"""
***************************************************************************
    SwmmAlgorithm.py
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
import re
import datetime
import codecs
import subprocess
from qgis.core import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import \
        GeoAlgorithmExecutionException
from processing.core.ProcessingLog import ProcessingLog
from processing.parameters.ParameterVector import ParameterVector
from processing.parameters.ParameterTable import ParameterTable
from processing.parameters.ParameterString import ParameterString
from processing.parameters.ParameterNumber import ParameterNumber
from processing.parameters.ParameterFile import ParameterFile
from processing.parameters.Parameter import Parameter
from processing.outputs.OutputVector import OutputVector
from processing.outputs.OutputTable import OutputTable
from processing.core.ProcessingConfig import ProcessingConfig
from processing.tools import dataobjects

def convert_date(d):
    month = {'JAN':'01',
             'FEB':'02',
             'MAR':'03',
             'APR':'04',
             'MAY':'05',
             'JUN':'06',
             'JUL':'07',
             'AUG':'08',
             'SEP':'09',
             'OCT':'10',
             'NOV':'11',
             'DEC':'12'}
    m = re.search('^(\S+)-(\d\d)-(\d\d\d\d)$',d) # for date and time saved as timestamps
    if not m : raise RuntimeError
    return m.group(3)+'-'+month[m.group(1)]+'-'+m.group(2)

class SwmmAlgorithm(GeoAlgorithm):

    TITLE = 'TITLE'
    OPTIONS = 'OPTIONS' # analysis options
    REPORT = 'REPORT' # output reporting instructions
    FILES = 'FILES' # interface file options
    RAINGAGES = 'RAINGAGES' # rain gage information
    HYDROGRAPHS = 'HYDROGRAPHS' # unit hydrograph data used to construct RDII inflows
    EVAPORATION = 'EVAPORATION' # evaporation data
    TEMPERATURE = 'TEMPERATURE' # air temperature and snow melt data
    SUBCATCHMENTS = 'SUBCATCHMENTS' # basic subcatchment information
    SUBAREAS = 'SUBAREAS' # subcatchment impervious/pervious sub-area data
    INFILTRATION = 'INFILTRATION' # subcatchment infiltration parameters
    LID_CONTROLS = 'LID_CONTROLS' # low impact development control information
    LID_USAGE = 'LID_USAGE' # assignment of LID controls to subcatchments
    AQUIFERS = 'AQUIFERS' # groundwater aquifer parameters
    GROUNDWATER = 'GROUNDWATER' # subcatchment groundwater parameters
    SNOWPACKS = 'SNOWPACKS' # subcatchment snow pack parameters
    JUNCTIONS = 'JUNCTIONS' # junction node information
    OUTFALLS = 'OUTFALLS' # outfall node information
    DIVIDERS = 'DIVIDERS' # flow divider node information
    STORAGE = 'STORAGE' # storage node information
    CONDUITS = 'CONDUITS' # conduit link information
    PUMPS = 'PUMPS' # pump link information
    ORIFICES = 'ORIFICES' # orifice link information
    WEIRS = 'WEIRS' # weir link information
    OUTLETS = 'OUTLETS' # outlet link information
    XSECTIONS = 'XSECTIONS' # conduit, orifice, and weir cross-section geometry
    TRANSECTS = 'TRANSECTS' # transect geometry for conduits with irregular cross-sections
    LOSSES = 'LOSSES' # conduit entrance/exit losses and flap valves
    CONTROLS = 'CONTROLS' # rules that control pump and regulator operation
    POLLUTANTS = 'POLLUTANTS' # pollutant information
    LANDUSES = 'LANDUSES' # land use categories
    COVERAGES = 'COVERAGES' # assignment of land uses to subcatchments
    BUILDUP = 'BUILDUP' # buildup functions for pollutants and land uses
    WASHOFF = 'WASHOFF' # washoff functions for pollutants and land uses
    TREATMENT = 'TREATMENT' # pollutant removal functions at conveyance system nodes
    INFLOWS = 'INFLOWS' # external hydrograph/pollutograph inflow at nodes
    DWF = 'DWF' # baseline dry weather sanitary inflow at nodes
    PATTERNS = 'PATTERNS' # periodic variation in dry weather inflow
    RDII = 'RDII' # rainfall-dependent I/I information at nodes
    LOADINGS = 'LOADINGS' # initial pollutant loads on subcatchments
    CURVES = 'CURVES' # x-y tabular data referenced in other sections
    TIMESERIES = 'TIMESERIES' # time series data referenced in other sections

    NODE_OUTPUT = 'NODE_OUTPUT'
    LINK_OUTPUT = 'LINK_OUTPUT'
    NODE_TABLE_OUTPUT = 'NODE_TABLE_OUTPUT'
    
    def __init__(self):
        GeoAlgorithm.__init__(self)

    def getIcon(self):
        return QIcon(os.path.dirname(__file__) + '/swmm.png')

    def helpFile(self):
       return None 

    def commandLineName(self):
        return 'swmm:simulation'

    def defineCharacteristics(self):
        self.name = 'Simulate flow in storm water conveyance systems'
        self.group = 'Simulation'

        self.addParameter(ParameterString(self.TITLE, 'Title', 'Swmm Simulation'))

        self.addParameter(ParameterTable(self.OPTIONS, 'Analysis options', True))
        self.addParameter(ParameterTable(self.REPORT, 'Output reporting instructions', True))
        self.addParameter(ParameterTable(self.FILES, 'Interface file options', True))
        self.addParameter(ParameterTable(self.RAINGAGES, 'Rain gage information', True))
        self.addParameter(ParameterTable(self.HYDROGRAPHS, 'Unit hydrograph data used to construct RDII inflows', True))
        self.addParameter(ParameterTable(self.EVAPORATION, 'Evaporation data', True))
        self.addParameter(ParameterTable(self.TEMPERATURE, 'Air temperature and snow melt data', True))
        self.addParameter(ParameterVector(self.SUBCATCHMENTS, 'Basic subcatchment information', [ParameterVector.VECTOR_TYPE_POLYGON], True))
        self.addParameter(ParameterTable(self.SUBAREAS, 'Subcatchment impervious/pervious sub-area data', True))
        self.addParameter(ParameterTable(self.INFILTRATION, 'Subcatchment infiltration parameters', True))
        self.addParameter(ParameterTable(self.LID_CONTROLS, 'Low impact development control information', True))
        self.addParameter(ParameterTable(self.LID_USAGE, 'Assignment of LID controls to subcatchments', True))
        self.addParameter(ParameterTable(self.AQUIFERS, 'Groundwater aquifer parameters', True))
        self.addParameter(ParameterTable(self.GROUNDWATER, 'Subcatchment groundwater parameters', True))
        self.addParameter(ParameterTable(self.SNOWPACKS, 'Subcatchment snow pack parameters', True))
        self.addParameter(ParameterVector(self.JUNCTIONS, 'Junction node information', [ParameterVector.VECTOR_TYPE_POINT], True))
        self.addParameter(ParameterTable(self.OUTFALLS, 'Outfall node information', True))
        self.addParameter(ParameterVector(self.DIVIDERS, 'Flow divider node information', [ParameterVector.VECTOR_TYPE_POINT], True))
        self.addParameter(ParameterVector(self.STORAGE, 'Storage node information', [ParameterVector.VECTOR_TYPE_POINT], True))
        self.addParameter(ParameterVector(self.CONDUITS, 'Conduit link information', [ParameterVector.VECTOR_TYPE_LINE], True))
        self.addParameter(ParameterVector(self.PUMPS, 'Pump link information', [ParameterVector.VECTOR_TYPE_POINT], True))
        self.addParameter(ParameterVector(self.ORIFICES, 'Orifice link information', [ParameterVector.VECTOR_TYPE_POINT], True))
        self.addParameter(ParameterVector(self.WEIRS, 'Weir link information', [ParameterVector.VECTOR_TYPE_POINT], True))
        self.addParameter(ParameterVector(self.OUTLETS, 'Outlet link information', [ParameterVector.VECTOR_TYPE_POINT], True))
        self.addParameter(ParameterTable(self.XSECTIONS, 'Conduit, orifice, and weir cross-section geometry', True))
        self.addParameter(ParameterTable(self.TRANSECTS, 'Transect geometry for conduits with irregular cross-sections', True))
        self.addParameter(ParameterTable(self.LOSSES, 'Conduit entrance/exit losses and flap valves', True))
        self.addParameter(ParameterTable(self.CONTROLS, 'Rules that control pump and regulator operation', True))
        self.addParameter(ParameterTable(self.POLLUTANTS, 'Pollutant information', True))
        self.addParameter(ParameterTable(self.LANDUSES, 'Land use categories', True))
        self.addParameter(ParameterTable(self.COVERAGES, 'Assignment of land uses to subcatchments', True))
        self.addParameter(ParameterTable(self.BUILDUP, 'Buildup functions for pollutants and land uses', True))
        self.addParameter(ParameterTable(self.WASHOFF, 'Washoff functions for pollutants and land uses', True))
        self.addParameter(ParameterTable(self.TREATMENT, 'Pollutant removal functions at conveyance system nodes', True))
        self.addParameter(ParameterTable(self.INFLOWS, 'External hydrograph/pollutograph inflow at nodes', True))
        self.addParameter(ParameterTable(self.DWF, 'Baseline dry weather sanitary inflow at nodes', True))
        self.addParameter(ParameterTable(self.PATTERNS, 'Periodic variation in dry weather inflow', True))
        self.addParameter(ParameterTable(self.RDII, 'Rainfall-dependent I/I information at nodes', True))
        self.addParameter(ParameterTable(self.LOADINGS, 'Initial pollutant loads on subcatchments', True))
        self.addParameter(ParameterTable(self.CURVES, 'x-y tabular data referenced in other sections', True))
        self.addParameter(ParameterTable(self.TIMESERIES, 'Time series data referenced in other sections', True))


        self.addOutput(OutputVector(self.NODE_OUTPUT, 'Node output layer'))
        self.addOutput(OutputTable(self.NODE_TABLE_OUTPUT, 'Node output table'))
        self.addOutput(OutputVector(self.LINK_OUTPUT, 'Link output layer'))
        pass

    def checkBeforeOpeningParametersDialog(self):
        if not ProcessingConfig.getSetting('Swmm_CLI'):
            return 'Swmm command line tool is not configured.\n\
                Please configure it before running Swmm algorithms.'
        layers = dataobjects.getVectorLayers()
        for p in self.parameters:
            for layer in layers:
                if layer.name() == p.name.lower() :
                    self.setParameterValue(p.name, layer )

        return None
        
    def swmmTable(self, table_name):
        uri = self.getParameterValue(table_name)
        if not uri: return u''
        layer = dataobjects.getObjectFromUri(uri)
        pkidx = layer.dataProvider().pkAttributeIndexes()
        fields = ""
        for i,field in enumerate(layer.dataProvider().fields()): 
            if not i in pkidx: fields+=field.name()+"\t"

        tbl =u'['+table_name+']\n'\
            ';'+fields+'\n'
        for feature in layer.getFeatures():
            for i,v in enumerate(feature):
                if not i in pkidx: 
                    if str(v) != 'NULL':
                        m = re.search('^(\d\d\d\d)-(\d\d)-(\d\d) (\d\d:\d\d):\d\d',str(v)) # for date and time saved as timestamps

                        if m:
                            tbl += '/'.join(m.group(2,3,1))+'\t'+m.group(4)+'\t'
                        else:
                            tbl += str(v)+'\t'
                    else: tbl += '\t'
            tbl += '\n'
        tbl += '\n'
        return tbl;

    def swmmKeyVal(self, table_name, simul_title):
        uri = self.getParameterValue(table_name)
        if not uri: return u''
        layer = dataobjects.getObjectFromUri(uri)
        fields = []
        for i,field in enumerate(layer.dataProvider().fields()): 
            fields.append(field.name())

        tbl =u'['+table_name+']\n'
        found = False
        for feature in layer.getFeatures():
            if str(feature[0]) == simul_title:
                for i,v in enumerate(feature):
                    if i and str(v) != 'NULL': tbl += fields[i].upper()+'\t'+str(v)+'\n'
                    elif i : tbl += '\t'
                found = True
                tbl += '\n'
        tbl += '\n'
        if not found:
            raise GeoAlgorithmExecutionException(
                    "No simulation named '"+simul_title+"' in "+table_name)
        return tbl;

    def processAlgorithm(self, progress):
        swmm_cli = ProcessingConfig.getSetting('Swmm_CLI')
        if not swmm_cli:
            raise GeoAlgorithmExecutionException(
                    'Swmm command line toom is not configured.\n\
                     Please configure it before running Swmm algorithms.')

        folder = '/tmp' #ProcessingConfig.getSetting(ProcessingConfig.OUTPUT_FOLDER)
        filename = folder+'/swmm.inp'
        f = codecs.open(filename,'w',encoding='utf-8')
        f.write('[TITLE]\n')
        f.write(self.getParameterValue(self.TITLE)+'\n\n')

        f.write(self.swmmKeyVal(self.OPTIONS, self.getParameterValue(self.TITLE)))
        f.write(self.swmmKeyVal(self.REPORT,self.getParameterValue(self.TITLE)))
        f.write(self.swmmTable(self.FILES))
        f.write(self.swmmTable(self.RAINGAGES))
        f.write(self.swmmTable(self.HYDROGRAPHS))
        f.write(self.swmmKeyVal(self.EVAPORATION, self.getParameterValue(self.TITLE)))
        f.write(self.swmmTable(self.TEMPERATURE))
        f.write(self.swmmTable(self.SUBCATCHMENTS))
        f.write(self.swmmTable(self.SUBAREAS))
        f.write(self.swmmTable(self.INFILTRATION))
        f.write(self.swmmTable(self.LID_CONTROLS))
        f.write(self.swmmTable(self.LID_USAGE))
        f.write(self.swmmTable(self.AQUIFERS))
        f.write(self.swmmTable(self.GROUNDWATER))
        f.write(self.swmmTable(self.SNOWPACKS))
        f.write(self.swmmTable(self.JUNCTIONS))
        f.write(self.swmmTable(self.OUTFALLS))
        f.write(self.swmmTable(self.DIVIDERS))
        f.write(self.swmmTable(self.STORAGE))
        f.write(self.swmmTable(self.CONDUITS))
        f.write(self.swmmTable(self.PUMPS))
        f.write(self.swmmTable(self.ORIFICES))
        f.write(self.swmmTable(self.WEIRS))
        f.write(self.swmmTable(self.OUTLETS))
        f.write(self.swmmTable(self.XSECTIONS))
        f.write(self.swmmTable(self.TRANSECTS))
        f.write(self.swmmTable(self.LOSSES))
        f.write(self.swmmTable(self.CONTROLS))
        f.write(self.swmmTable(self.POLLUTANTS))
        f.write(self.swmmTable(self.LANDUSES))
        f.write(self.swmmTable(self.COVERAGES))
        f.write(self.swmmTable(self.BUILDUP))
        f.write(self.swmmTable(self.WASHOFF))
        f.write(self.swmmTable(self.TREATMENT))
        f.write(self.swmmTable(self.INFLOWS))
        f.write(self.swmmTable(self.DWF))
        f.write(self.swmmTable(self.PATTERNS))
        f.write(self.swmmTable(self.RDII))
        f.write(self.swmmTable(self.LOADINGS))
        f.write(self.swmmTable(self.CURVES))
        f.write(self.swmmTable(self.TIMESERIES))

        f.close()

        outfilename = folder+'/swmm.out'
        progress.setText('running simulation')
        log=""
        proc = subprocess.Popen(
            swmm_cli+" "+filename+" "+outfilename,
            shell=True,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=False,
            ).stdout
        for line in iter(proc.readline, ''):
            log+=line
        ProcessingLog.addToLog(ProcessingLog.LOG_INFO, log)

        if re.search('There are errors', log):
            o = open(outfilename,'r')
            ProcessingLog.addToLog(ProcessingLog.LOG_ERROR, o.read())
            o.close()
            raise RuntimeError('There were errors, look into logs for details')

        progress.setText('postprocessing output')

        # put features in a map indexed by the identifier (first column)
        layer = dataobjects.getObjectFromUri(self.getParameterValue(self.JUNCTIONS))
        node_fields = QgsFields()
        node_fields.append(QgsField('Node', QVariant.String))
        node_fields.append(QgsField('Time', QVariant.String))
        node_fields.append(QgsField('Inflow', QVariant.Double))
        node_fields.append(QgsField('Flooding', QVariant.Double))
        node_fields.append(QgsField('Depth', QVariant.Double))
        node_fields.append(QgsField('Head', QVariant.Double))
        node_feat = {}
        for feat in layer.getFeatures(): 
            if feat.geometry() and feat.geometry().exportToWkt(): 
                node_feat[feat.attributes()[0]] = feat

        node_writer = self.getOutputFromName(
                self.NODE_OUTPUT).getVectorWriter(node_fields.toList(),
                                                   QGis.WKBPoint,
                                                   layer.crs())
        node_table_writer = self.getOutputFromName(
                self.NODE_TABLE_OUTPUT).getTableWriter(node_fields.toList())

        layer = dataobjects.getObjectFromUri(self.getParameterValue(self.CONDUITS))
        link_fields = QgsFields()
        link_fields.append(QgsField('Link', QVariant.String))
        link_fields.append(QgsField('Time', QVariant.String))
        link_fields.append(QgsField('Flow', QVariant.Double))
        link_fields.append(QgsField('Velocity', QVariant.Double))
        link_fields.append(QgsField('Depth', QVariant.Double))
        link_fields.append(QgsField('PercentFull', QVariant.Double))
        link_feat = {}
        for feat in layer.getFeatures():
            if feat.geometry() and feat.geometry().exportToWkt(): 
                link_feat[feat.attributes()[0]] = feat

        link_writer = self.getOutputFromName(
                self.LINK_OUTPUT).getVectorWriter(link_fields.toList(),
                                                   QGis.WKBLineString,
                                                   layer.crs())

        # here we create output layers
        # it's a python implementation of a join
        # on the identifyer field between the results an the JUNCTIONS or PIPES
        # geometries
        total_size = os.path.getsize(outfilename)
        total_read = 0
        o = codecs.open(outfilename,'r',encoding='utf-8')
        # get nodes results
        link_id = '' 
        node_id = '' 
        line = o.readline()
        while line:
            line = line.rstrip()
            if (node_id or link_id) and not line: 
                link_id = ''
                node_id = ''
            if re.search('^  <<< Node ', line): 
                node_id = line[11:-4]
                for i in range(5): line = o.readline()
                line = line.rstrip()
            if re.search('^  <<< Link ', line): 
                link_id = line[11:-4]
                for i in range(5): line = o.readline()
                line = line.rstrip()
            if node_id:
                feature = QgsFeature(node_fields)
                tbl = line.split()
                if len(tbl) >= 6:
                    feature['Node']     = node_id
                    feature['Time']     = convert_date(tbl[0])+' '+tbl[1]
                    feature['Inflow']   = tbl[2]
                    feature['Flooding'] = tbl[3]
                    feature['Depth']    = tbl[4]
                    feature['Head']     = tbl[5]
                    feat = node_feat.get(node_id, None)
                    if feat : feature.setGeometry(feat.geometry())
                    node_writer.addFeature(feature)
                    node_table_writer.addRecord([node_id]+tbl)
            if link_id:
                feature = QgsFeature(link_fields)
                tbl = line.split()
                if len(tbl) >= 6:
                    feature['Link']     = link_id
                    feature['Time']     = convert_date(tbl[0])+' '+tbl[1]
                    feature['Flow']     = tbl[2]
                    feature['Velocity'] = tbl[3]
                    feature['Depth']    = tbl[4]
                    feature['PercentFull'] = tbl[5]
                    feat = link_feat.get(link_id, None)
                    if feat : feature.setGeometry(feat.geometry())
                    link_writer.addFeature(feature)
            line = o.readline()
            total_read += len(line)
            progress.setPercentage(int(100*total_read/total_size))

        o.close()
        
