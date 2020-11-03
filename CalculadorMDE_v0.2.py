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
# from termcolor import cprint 
from astropy.table import Table, vstack
from colorama import Fore, Style, init, deinit, reinit

import matplotlib.pyplot as plt
import tkinter as Tk
from tkinter import simpledialog
# from tkinter import filedialog

#%% Definición de constantes
version = '0.2'
author  = 'Matias Martini'
oufFileTail = '_MDE.txt'
name = 'Herramientas GORA'
figs = False 

#%% Definición de funciones

## Extrae JD y magnitud medida de un informe de FotoDif
# Recibe como entrada la ruta del archivo "fullFileName" y devuelve dos listas, 
# "julianDate" con la fecha fuliana de la medición y "mag" con las magnitudes 
# medidas.
def getDataFromFotoDiffInform(inputInformFFName):   
    f = open(inputInformFFName,'r')    
    payloadLinesCntr = -1                          # Contaddor de líneas útiles de infome. Es <0 hasta que se detectan los guiones
    julianDate = []                                 # Lista para JD
    mag = []                                        # Lista para Magnitud
    while True:                                     # Ciclo desde el princiío hasta \n luego de las mediciones
        linea = f.readline()                        # Lee linea
        if payloadLinesCntr >=0:                    # Si esta en la zona útil del informe
            if linea == '\n':                       # Si en la zona util deteccta \n finaliza
                break
            payloadLinesCntr=+1                     # Incrementa contador de líneas utiles
            parsedLine = linea.split()              # Pasea linea a una lista con cadda uno de los campos, en la posicion 0 queda JD, en la 1 Mag, en la 2 error de mag y en las siguientes posiciones los datos de la estrella de control o lo que sea que se haya agregado.
            julianDate.append(float(parsedLine[0])) # Agrega dato de JD a lista
            mag.append(float(parsedLine[1]))        # Magnitud medida 
        if linea[0:34] == '----------------------------------': # Cuando detecta guiones asume inicio de datos  y pone contaddor a 0
            payloadLinesCntr = 0     
    f.close()
    assert len(julianDate) == len(mag)              # Verifica que ambas listas tengan el mismo largo.
    
    # Identifica etiqueta observacion
    try:
        fileName = inputInformFFName[inputFullFileName.rfind('/')+1:-4]
        idx = [i for i, a in enumerate(fileName) if a == '_']
        observTag = fileName[idx[1]+1:idx[5]]
    except:
        observTag = ''
    
    return julianDate, mag, observTag

# Reescribe archivo
def rewriteMagFotoDiffInform(inputInformFFName, outputInformFFName, newMag, s_stdJD, s_stdMag):      
    inputFile  = open(inputInformFFName,'r')
    outputFile = open(outputInformFFName ,'w')

    fileSection = 0
    
    linea = inputFile.readline()
    outputFile.writelines('FOTOMETRIA DIFERENCIAL ESTANDARIZADA - GORA\n')
    while True:
        linea = inputFile.readline()
        if not linea:        # Si es el final del archivo    
            break
        
        if fileSection == 0:      # Si es la parte inicial del achivo
            outputFile.writelines(linea)
            if linea[0:34] == '----------------------------------':
                fileSection = 1
                j = 0
                continue
            
        if fileSection == 1:         # Si es la parte media del archivo, donde está la carga util
            if linea == '\n':
                outputFile.writelines(linea)
                fileSection = 3
                continue

            parsedLine = (linea.split())
            parsedLine[1] = newMag[j]
            outputFile.writelines([parsedLine[0] + '      ' 
                                 + '%.3f' % parsedLine[1] + '    ' 
                                 + parsedLine[2]+'\n'] )
            j=j+1
            
        if fileSection == 3:         # Si es la parte final del archivo
            outputFile.writelines(linea)
            
    inputFile.close()
    
    outputFile.writelines('\nProcesado con ' + name + ' versión ' + version + '\n')
    outputFile.writelines('Fecha de estandarización: ' + s_stdJD + '\n')
    outputFile.writelines('Magnitud de estandarización: ' + s_stdMag + '\n')

    outputFile.close()

# Obtiene efemerides de JPL Horizons
def Magnitude_JPL_Horizons_Query(target, epochList):
    queryLoc   = '500'                              # Ubicación Geocentrica
    
    jdKey = 'datetime_jd'                           # Nombre de colunma de JD en tabla
    vmagKey = 'V'                                   # Nombre de colunma de Magnitud en tabla
    
    # JPL Horizons Query
    obj = Horizons(id=target, id_type = 'smallbody',location = queryLoc, epochs=epochList)
    eph = obj.ephemerides()                         # Obtiene 
    return(eph['targetname'][0],  eph[jdKey,vmagKey])                      # Se arma nueva tabla con JD y Mag

def printError(text):
    reinit()
    print(Fore.RED + '[ERROR] ' + text + Style.RESET_ALL)
    deinit()
    
def printWarning(text):
    reinit()
    print(Fore.YELLOW + '[ERROR] ' + text + Style.RESET_ALL)
    deinit()

#%% Selección de opciones y configuración inicial
init()
deinit()
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
print('        (9) Salir.',sep='')
opc = 0
while True:
    opc = input('      Ingrese opción:')
    if opc in ['1','2','9']:
        break
    
# Especificación de archivos a convertir
if   opc ==  '1':           # (1) Convertir un archivo.
    inputFileDir =''
    inputFileName = [input('    * Ingrese nombre del archivo a convertir:')]
    if not os.path.isfile('./' + inputFileName[0]):
        printError('El archivo '+ inputFileName[0] + ' no existe en el directorio ' + 
               os.getcwd())
        input("Presione Enter para salir.")
        sys.exit()         

elif opc ==  '2':           # (2) Convertir un conjunto de archivos.
    inputFileDir =  input('    * Ingrese nombre de la carpeta que contiene los archivos:') 
    inputFileDir = inputFileDir +'/'
    extensions = ['.txt', '.TXT']
    try:
        inputFileName = [f for f in os.listdir(inputFileDir) if os.path.splitext(f)[1] in extensions]
    except:
        printError('El directorio no existe en '+ os.getcwd())
        input("Presione Enter para salir.")
        sys.exit()     
    if len(inputFileName)==0:
        printError('No existen archivos ".txt" en el directorio ' + 
                   os.getcwd() + '/' + inputFileDir)
        input("Presione Enter para salir.")
        sys.exit()
 
elif opc ==  '9':           # (9) salir.
    sys.exit()

# Confirmación de archivos a procesar 
Ninf = len(inputFileName)
print('\n    * Se procesará/n '+ str(Ninf) +' informe/s.')
print('     - ', end = '')
print(*inputFileName, sep='\n     - ')

while True:
    opc = input('    * Ingrese 1 para continuar o 9 para salir:')
    if opc in ['1','9']:
        break

if opc == '9':              # (9) salir.
    sys.exit()
      
# Especificación de modo de fecha   
print('    * Ingrese modo de fecha:') 
print('        (1) Hora de estandarización igual 00:00:00 UTC.')
print('        (2) Hora de estandarización igual a hora de captura.')
print('        (9) Salir.')
while True:
    stdMode = input('      Ingrese opción:')
    if stdMode in ['1','2','9']:
        break
   
if stdMode == '9':          # (9) salir.
    sys.exit()    

# Especificación/oobtención de ID de objeto    
objectID = input('    * Ingrese ID de objeto o deje en blanco para reconocer del nombre de archivo:') 
if not objectID:
    objectID = inputFileName[0][0:inputFileName[0].find('_')]     

while True:
    opcFig = input('    * Desea generar figuras? [Si/no]:')
    if opcFig in ['Si', 'si', 'SI', 'S', 's', '']:
        figs = True
        break
    if opcFig in ['No', 'no', 'NO', 'N', 'n']:
        figs = False
        break
    
#%% Inicio de procesamiento
print('\n------------------------------------------------------------------------------')    
print('                          * Inicio de procesamiento *                         \n')

# Se define el nombre del directorio de salida de informes y si no existe lo crea
outputFileDir =  inputFileDir[0:-1] + oufFileTail[0:-4] +'/'
tepDir = os.path.join('./',outputFileDir)
if not os.path.exists(tepDir):
    os.mkdir(tepDir)

# Se define el nombre del directorio de salida de efemérides y si no existe lo crea
ephOutputFileDir =  outputFileDir + 'Efemerides' +'/'
tepDir = os.path.join('./',ephOutputFileDir)
if not os.path.exists(tepDir):
    os.mkdir(tepDir)    
    
ephTable = Table()

# # Inicializa figuras
if figs:  
    plt.figure(num=1, figsize=(10, 6), dpi=150, facecolor='w', edgecolor='k')
    plt.figure(num=2, figsize=(10, 6), dpi=150, facecolor='w', edgecolor='k')
    m = 5;
    mkr = 100 * ('ov+s*x2pd')

#%% Modo 1: Hora de estandarización igual 00:00:00 UTC.')   
if stdMode == '1':
    
# Identificación de fechas de estandariza
    print('* Identificación de fechas de estandarización')
    
    standarizationDate = []             # Almacena fechas de estanadrización para pedir efemerides    
    for informe in inputFileName:
        print(' - Procesando: ' + informe)        
        inputFullFileName = ('./' + inputFileDir + informe)        
        # Obtiene datos de JD y Mag del informe
        infJD, infM, _ = getDataFromFotoDiffInform(inputFullFileName)
        # Calculo de fecha de estandarización de mediciones del informe
        # Se asume dia de la medición a las 00:00:00 UTC
        infStadarizationDate = (np.unique(np.floor(np.array(infJD)))+0.5)
        # Array de fechas de estandarización
        standarizationDate.append(infStadarizationDate) # Se podría haber usado un set
        print('   Fecha/s de estandarización:',end=' ')
        print(infStadarizationDate)
     
    # Se concatena, eliminan repetidos y ordena la lista
    standarizationDate = np.sort(np.unique(np.concatenate(standarizationDate, axis=0 )))
    print('')    

# Descarga de efemerides de JPL Horizons
    print('* Descarga de efemérides de JPL HORIZONS' )    
    ephFileName = objectID + '_JPL_Horizons_EfeMag-EstJD.txt' 
    strobjectID, stdMagEphem = Magnitude_JPL_Horizons_Query(objectID, list(standarizationDate))
    stdMagEphem.add_index('datetime_jd')                            # Hace indice la columna de JD
    # print('Efemerides para: ' + strobjectID + '\n')
    # print(stdMagEphem)
    ephTable = vstack([ephTable, stdMagEphem])

    stdMagEphem.write(ephOutputFileDir + ephFileName, format='ascii',overwrite=True)
    print(' - Efemérides guardades en: '+ ephFileName, end = '\n \n')

# Calculo de Magnitid Diferencial Estandarizada
    infCntr = 0
    for informe in inputFileName:
        infCntr+=1
        print('* Procesando informe ' + str(infCntr) + ' de ' + str(Ninf) + ': ' + informe)
        
        inputFullFileName = ('./' + inputFileDir + informe)
        outputFullFileName = ('./' + outputFileDir + informe[0:-4] + oufFileTail)
        
        print(' - Cargando informe' )
        infJD, infM, obsTag = getDataFromFotoDiffInform(inputFullFileName)  # Obtiene datos de JD y Mag del informe
        if figs:  
            plt.figure(1)
            plt.scatter(infJD, infM, label = obsTag, marker = mkr[infCntr-1])   # Agrega puntos

        print(' - Calculando de MDE')     
        N = len(infJD)                         # Cantidad de medidas en informe
        infStadarizationDate = (np.floor(np.array(infJD)))+0.5
        stdMag = np.zeros(N)                    # Vector de mag de estandarización
        MagDifEst = np.zeros(N)                 # Vector de mag diferenccial estandarizada
        for i in range(N):                      # Para cada fila del informe
                                                # Busca la mag de estandarización en las efemerides
            stdMag[i] = stdMagEphem.loc[infStadarizationDate[i]]['V']
            MagDifEst[i] = infM[i] - stdMag[i]  # Calcula mag diferencial estandarizada
        
        if figs:  
            plt.figure(2)
            plt.scatter(infJD, MagDifEst, label = obsTag, marker = mkr[infCntr-1])   # Agrega puntos

        # Se generan vectores que contienen las JD  y magnitudes usadas para
        # estanddarizar este informe
        str_stdJD  = ' '.join(str(e) for e in np.unique(infStadarizationDate).tolist())
        str_stdMag = ' '.join(str(e) for e in np.unique(stdMag).tolist())
    
        # Reescribe el archivo con las mag diferenciales rizadas y agrega
        # información sobre JD y mag de estandarización usada en el informe.
        rewriteMagFotoDiffInform(inputFullFileName, outputFullFileName, MagDifEst, str_stdJD, str_stdMag)
        print(' - Informe con MDE guardado en: '+ outputFullFileName, end = '\n \n')

#%% Modo 2: Hora de estandarización igual a hora de captura.
if stdMode == '2':
    infCntr = 0
    for informe in inputFileName:
        infCntr+=1
        print('* Procesando informe ' + str(infCntr) + ' de ' + str(Ninf) + ': ' + informe)
        
        inputFullFileName = ('./' + inputFileDir + informe)
        outputFullFileName = ('./' + outputFileDir + informe[0:-4] + oufFileTail)
        ephFileName = informe[0:-4] + '_EfemJPL.txt'
        
        print(' - Cargando informe' )
        infJD, infM, obsTag = getDataFromFotoDiffInform(inputFullFileName)  # Obtiene datos de JD y Mag del informe
        if figs:  
            plt.figure(1)
            plt.scatter(infJD, infM, label = obsTag, marker = mkr[infCntr-1])   # Agrega puntos

        print(' - Descarga de efemérides de JPL HORIZONS' )
        strobjectID, stdMagEphem = Magnitude_JPL_Horizons_Query(objectID, infJD)
        ephTable = vstack([ephTable, stdMagEphem])
       
        stdMagEphem.write(ephOutputFileDir + ephFileName, format='ascii',overwrite=True)
        print(' - Efemérides guardades en: '+ ephFileName)

        print(' - Calculando de MDE')
        stdMag = np.array(stdMagEphem['V'])
        assert len(infM) == len(stdMag)
        assert infJD == list(np.array(stdMagEphem['datetime_jd']))
        MagDifEst = infM - stdMag
        if figs:  
            plt.figure(2)
            plt.scatter(infJD, MagDifEst, label = obsTag, marker = mkr[infCntr-1])   # Agrega puntos

        rewriteMagFotoDiffInform(inputFullFileName, outputFullFileName, MagDifEst, ephFileName, ephFileName)
        print(' - Informe con MDE guardado en: '+ outputFullFileName, end = '\n\n')

#%% Gráficos
if figs: 
    # Efemérides para JD minimo -5 y JD maximo +5 días       
    plt.figure(1)
    plt.plot(ephTable['datetime_jd'],ephTable['V'],'b',label='Efemérides')
    plt.ylim(reversed(plt.ylim()))                      # flip the y-axis
    plt.xlabel("$Fecha~Juliana~[dia]$", fontsize=12)
    plt.ylabel("$Magnitud [V]$", fontsize=12)
    plt.grid()
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left', ncol=3, mode="expand", borderaxespad=0.)
    plt.savefig(outputFileDir + objectID + '_Mag-JD.png',dpi =150,bbox_inches = "tight")
    
    plt.figure(2)
    plt.plot(ephTable['datetime_jd'],len(ephTable['datetime_jd']) * [0],'b',label='Referencia')
    plt.ylim(reversed(plt.ylim()))                      # flip the y-axis
    plt.xlabel("$Fecha~Juliana~[dia]$", fontsize=12)
    plt.ylabel("$MDE [V]$", fontsize=12)
    plt.grid()
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left', ncol=3, mode="expand", borderaxespad=0.)
    plt.savefig(outputFileDir + objectID + '_MDE-JD.png',dpi =150,bbox_inches = "tight")
           
#%% FIN
print('------------------------------------------------------------------------------')
print('    * Se procesaron correctamente ' + str(Ninf) + ' informes de ' + strobjectID +  '.')
input('    * Presione Enter para salir.') 

#%%% NOTAS

# Había algunos problemas con el parseo de las efemerides, se solucionó 
# utilzando la versión de desarrollo de Astroquery 
# astroquery                         0.4.2.dev0
# pip install --pre astroquery

