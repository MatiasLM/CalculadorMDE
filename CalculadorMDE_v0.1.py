# -*- coding: utf-8 -*-
"""
Created on Fri Oct 23 20:20:52 2020

@author: Matias
"""

import os
import sys
import numpy as np
from astroquery.jplhorizons import Horizons
# https://astroquery.readthedocs.io/en/latest/jplhorizons/jplhorizons.html#

#%% Definición de constantes
version = '0.1'
author  = 'Matias Martini'
oufFileTail = '_MDE.txt'
name = 'Herramientas GORA'

#%% Definición de funciones

# Extrae JD y magnitud medida de un informe de FotoDif
def getDataFromFotoDiffInform(fullFileName):   

    f = open(fullFileName,'r')
    payloadFlag = -1;
    julianDate = []
    mag = []
    while True:
        linea = f.readline()
        if payloadFlag >=0:
            if linea == '\n':
                break
            payloadFlag=+1
            parsedLine = linea.split()
            julianDate.append(float(parsedLine[0]))      # Fecha juliana de la captura
            mag.append(float(parsedLine[1]))      # Magnitud medida 
        if linea[0:34] == '----------------------------------':
            payloadFlag = 0;     
    f.close()
    assert len(julianDate) == len(mag)
    return julianDate, mag

# Reescribe archivo
def rewriteMagFotoDiffInform(inputFullFileName, outputFullFileName, newMag, stdJD, stdMag):   
    
    inputFile  = open(inputFullFileName,'r')
    outputFile = open(outputFullFileName ,'w')

    fileSection = 0;

    linea = inputFile.readline()
    outputFile.writelines('FOTOMETRIA DIFERENCIAL ESTANDARIZADA - GORA\n')
    while True:
        linea = inputFile.readline()
        if not linea:        # Si es el final del archivo    
            break
        
        if (fileSection == 0):      # Si es la parte inicial del achivo
            outputFile.writelines(linea)
            if linea[0:34] == '----------------------------------':
                fileSection = 1;
                i = 0;
                continue
            
        if fileSection == 1:         # Si es la parte media del archivo, donde está la carga util
            if linea == '\n':
                outputFile.writelines(linea)
                fileSection = 3;
                continue

            parsedLine = (linea.split())
            parsedLine[1] = newMag[i];
            outputFile.writelines([parsedLine[0] + '      ' 
                                 + '%.3f' % parsedLine[1] + '    ' 
                                 + parsedLine[2]+'\n'] )
            i=i+1;
            
        if fileSection == 3:         # Si es la parte final del archivo
            outputFile.writelines(linea)
            
    inputFile.close()
    
    outputFile.writelines('\nProcesado con ' + name + ' versión ' + version + '\n')
    outputFile.writelines('Fecha de estandarización: ' + stdJD + '\n')
    outputFile.writelines('Magnitud de estandarización: ' + stdMag + '\n')

    outputFile.close()

# Obtiene efemerides de JPL Horizons
def Magnitude_JPL_Horizons_Query(target, epochList):
    queryLoc   = '500';                             # Ubicación Geocentrica
    
    jdKey = 'datetime_jd';                          # Nombre de colunma de JD en tabla
    vmagKey = 'V';                                  # Nombre de colunma de Magnitud en tabla
    
    # JPL Horizons Query
    obj = Horizons(id=target, id_type = 'smallbody',location = queryLoc, epochs=epochList);
    eph = obj.ephemerides();                        # Obtiene efemerides
    return(eph['targetname'][0],  eph[jdKey,vmagKey])                      # Se arma nueva tabla con JD y Mag


#%% Selección de opciones y configuración inicial
print('******************************************************************************')
print('**                                                                          **')
print('**                          - Herramientas GORA -                           **')
print('**          Calculador de Magnitid Diferencial Estandarizada (MDE)          **')
print('**                                                                          **')
print('**   Versión ' + version + '                                   Autor: ' + author + '    **')
print('******************************************************************************')
print('\n')
print('    * Que desea hacer:')
print('        (1) Convertir un archivo.')
print('        (2) Convertir un conjunto de archivos.')
print('        (9) Salir.')
opc = 0;
while True:
    opc = input('      Ingrese opción:')
    if opc in ['1','2','9']:
        break

# Especificación de archivos a convertir
if   opc ==  '1':           # (1) Convertir un archivo.
    inputFileDir ='';
    inputFileName = [input('    * Ingrese nombre del archivo a convertir:')]

elif opc ==  '2':           # (2) Convertir un conjunto de archivos.
    inputFileDir =  input('    * Ingrese nombre de la carpeta que contiene los archivos:') 
    inputFileDir = inputFileDir +'/'
    extensions = ['.txt', '.TXT']
    inputFileName = [f for f in os.listdir(inputFileDir) if os.path.splitext(f)[1] in extensions]
 
elif opc ==  '9':           # (9) salir.
    sys.exit();

# Confirmación de archivos a procesar 
Ninf = len(inputFileName)
print('\n    * Se procesará/n '+ str(Ninf) +' informe/s. \n')
print(' - ', end = ''),
print(*inputFileName, sep='\n - ')

while True:
    opc = input('    * Ingrese 1 para continuar o 9 para salir:')
    if opc in ['1','9']:
        break

if opc == '9':              # (9) salir.
    sys.exit();

# Especificación/oobtención de ID de objeto    
ObjectID = input('    * Ingrese ID de objeto o deje en blanco para reconocer del nombre de archivo:') 
if not ObjectID:
    ObjectID = inputFileName[0][0:inputFileName[0].find('_')]     
    
  
#%% Inicio de procesamiento
print('\n------------------------------------------------------------------------------')    
print('                          * Inicio de procesamiento *                         ')

# Se define el nombre del directorio de salida y si no existe lo crea
outputFileDir =  inputFileDir[0:-1] + oufFileTail[0:-4] +'/'
dir = os.path.join('./',outputFileDir)
if not os.path.exists(dir):
    os.mkdir(dir)
    

#%% Identificación de fechas
print('\n------------------------------------------------------------------------------')    
print('                * Identificación de fechas de estandarización *               \n')

standarizationDate = []             # Almacena fechas de estanadrización para pedir efemerides

for informe in inputFileName:
    print('- Procesando: ' + informe)
    
    fullFileName = ('./' + inputFileDir + informe)
    
    # Obtiene datos de JD y Mag del informe
    infJD, infM = getDataFromFotoDiffInform(fullFileName)
    # Calculo de fecha de estandarización de mediciones del informe
    # Se asume dia de la medición a las 00:00:00 UTC
    infStadarizationDate = (np.unique(np.floor(np.array(infJD)))+0.5)
    # Array de fechas de estandarización
    standarizationDate.append(infStadarizationDate) # Se podría haber usado un set
    print('   Fecha/s de estandarización:',end=' ')
    print(infStadarizationDate)
 
# Se concatena, eliminan repetidos y ordena la lista
standarizationDate = np.sort(np.unique(np.concatenate(standarizationDate, axis=0 )))

#%% Descarga de efemerides de JPL Horizons
print('\n------------------------------------------------------------------------------')    
print('                  *  Descarga de efemerides de JPL Horizons *                 \n')

# Query
strObjectID, tMagEphem = Magnitude_JPL_Horizons_Query(ObjectID, list(standarizationDate))
tMagEphem.add_index('datetime_jd')  # Hace indice la columna de JD
print('Efemerides para: ' + strObjectID + '\n')
print(tMagEphem)

tMagEphem.write(outputFileDir + ObjectID + '_JPL_Horizons_EfeMag-EstJD.txt', format='ascii',overwrite=True)

#%% Calculo de Magnitid Diferencial Estandarizada
print('\n------------------------------------------------------------------------------')
print('              * Calculo de Magnitid Diferencial Estandarizada *               \n')

for informe in inputFileName:                 # Para cada informe
    print('- Procesando: ' + informe)
    
    inputFullFileName = ('./' + inputFileDir + informe)
    outputFullFileName = ('./' + outputFileDir + informe[0:-4] + oufFileTail)
    
    # Obtiene datos de los informes
    infJD, infM = getDataFromFotoDiffInform(inputFullFileName)
    
    N = len(infJD);                         # Cantidad de medidas en informe
    infStadarizationDate = (np.floor(np.array(infJD)))+0.5
    stdMag = np.zeros(N)                    # Vector de mag de estandarización
    MagDifEst = np.zeros(N)                 # Vector de mag diferenccial estandarizada
    for i in range(N):                      # Para cada fila del informe
                                            # Busca la mag de estandarización en las efemerides
        stdMag[i] = tMagEphem.loc[infStadarizationDate[i]]['V']
        MagDifEst[i] = infM[i] - stdMag[i]  # Calcula mag diferencial estandarizada
    
    # Se generan vectores que contienen las JD  y magnitudes usadas para
    # estanddarizar este informe
    str_stdJD  = ' '.join(str(e) for e in np.unique(infStadarizationDate).tolist())
    str_stdMag = ' '.join(str(e) for e in np.unique(stdMag).tolist())

    # Reescribe el archivo con las mag diferenciales rizadas y agrega
    # información sobre JD y mag de estandarización usada en el informe.
    rewriteMagFotoDiffInform(inputFullFileName, outputFullFileName, MagDifEst, str_stdJD, str_stdMag)
    
    print('  Archivo de salida: ' + outputFullFileName)
    
#%% FIN
print('\n------------------------------------------------------------------------------')
input('    * Proccesamiento finalizado, presione Enter para salir.') 


#%%% NOTAS

# Había algunos problemas con el parseo de las efemerides, se solucionó 
# utilzando la versión de desarrollo de Astroquery 
# astroquery                         0.4.2.dev0