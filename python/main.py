import sqlite3
import pandas as pd
import numpy as np
import SqlOperations
import tkinter as tk
import tkinter.filedialog as fd

'''

TODO: 

File reader object, which automaticly uses newest files avalible, or can choose them manualy via gui.

Simple gui for files
 
Improve readbility of code

Add comments

'''

def clone( list ): return list[:]


def transformCSVtoSqliteFormat(columnList, mainList): 
    
    formatedList = [] 
    
    for i in range( len( columnList ) ): 
        
        col = columnList[i] 
        
        for row in mainList: 
            
            tmpList = [ col ] + [ str( val ) for val in row[ :2 ] ] + ( [ str(row[ i + 2 ] ) ] if i + 2 < len( row ) else [] )
            
            formatedList.append(tmpList) 
    
    return formatedList


def loadFiles():

    fileList = list( fd.askopenfilenames(parent=tk.Tk(), title='Choose 5 corresponding files') )

    if len( fileList ) != 5: 

        raise Exception("Must select 5 files to continue")
   
    fileList.sort()

    return fileList

   
def main():
  
    #0 - generators, 1 - nodes, 2 - q, 3 - transformers, 4 - v
    fileList = loadFiles()

    try: 

        with sqlite3.connect("sql/SORNDatabase.db") as connection:

            database = SqlOperations.SqlOperations( connection )

            query = '''BEGIN;

                DROP TABLE IF EXISTS Nodes_generators;

                DROP TABLE IF EXISTS Nodes_transformers;

                DROP TABLE IF EXISTS Nodes_voltage_changes;

                DROP TABLE IF EXISTS Elements_reactive_power_changes;

                COMMIT;'''

            database.executeScript( query )

            query = '''BEGIN;
                     
                CREATE TABLE IF NOT EXISTS "Nodes"(

                    [name] NVARCHAR(16) PRIMARY KEY NOT NULL,

                    [min_voltage] REAL NOT NULL,

                    [current_voltage] REAL NOT NULL,

                    [max_voltage] REAL NOT NULL,

                    [in_model] BOOLEAN NOT NULL
                );
                     
                CREATE TABLE IF NOT EXISTS "Generators"(

                    [name] NVARCHAR(16) PRIMARY KEY NOT NULL,

                    [min_active_power] REAL NOT NULL,

                    [current_active_power] REAL NOT NULL,

                    [max_active_power] REAL NOT NULL,

                    [min_reactive_power] REAL NOT NULL,

                    [current_reactive_power] REAL NOT NULL,

                    [max_reactive_power] REAL NOT NULL,

                    [in_model] BOOLEAN NOT NULL
                );
                     
                CREATE TABLE IF NOT EXISTS "Transformers"(

                    [name] NVARCHAR(16) PRIMARY KEY NOT NULL,

                    [min_tap] INTEGER NOT NULL,

                    [current_tap] INTEGER NOT NULL,

                    [max_tap] INTEGER NOT NULL,

                    [regulation_step] REAL NOT NULL,

                    [in_model] BOOLEAN NOT NULL
                );
                                    
                CREATE TABLE IF NOT EXISTS "Nodes_generators"(

                    [id] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,

                    [node] NVARCHAR(16) NOT NULL,

                    [generator] NVARCHAR(16) NOT NULL,

                    FOREIGN KEY(node) REFERENCES Nodes(name),

                    FOREIGN KEY(generator) REFERENCES Generators(name)
                );

                CREATE TABLE IF NOT EXISTS "Nodes_transformers"(

                    [id] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,

                    [node] NVARCHAR(16) NOT NULL,

                    [transformer] NVARCHAR(16) NOT NULL,

                    FOREIGN KEY(node) REFERENCES Nodes(name),

                    FOREIGN KEY(transformer) REFERENCES Transformers(name)
                );

                CREATE TABLE IF NOT EXISTS "Elements_reactive_power_changes"(

                    [id] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,

                    [base_element] NVARCHAR(16) NOT NULL,

                    [base_element_reactive_power_difference] REAL NOT NULL,

                    [changed_element] NVARCHAR(16) NOT NULL,

                    [changed_element_difference] REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS "Nodes_voltage_changes"(

                    [id] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,

                    [node] NVARCHAR(16) NOT NULL,

                    [changed_element] NVARCHAR(16) NOT NULL,

                    [node_voltage_difference] REAL NOT NULL,

                    [changed_element_difference] REAL NOT NULL,

                    FOREIGN KEY (node) REFERENCES Nodes(name)
                );

                COMMIT;

                BEGIN;

                UPDATE Nodes SET in_model = False;

                UPDATE Generators SET in_model = False;

                UPDATE Transformers SET in_model = False;

                COMMIT;'''

            database.executeScript( query )

            query = '''Generators(name,min_active_power,current_active_power,max_active_power,min_reactive_power,current_reactive_power,max_reactive_power,in_model ) 
VALUES (?, ?, ?, ?, ?, ?, ?,True);'''
            
            generators = pd.read_csv( fileList[ 0 ] ).to_numpy().tolist()

            nodesGenerators = np.delete( clone( generators ), (1, 2, 3, 4, 5, 6), axis=1 )

            database.insertOrReplaceInto( query, generators, True )

            transformers = pd.read_csv( fileList[ 3 ] ).to_numpy().tolist()

            nodesTransformers = np.delete( clone( transformers ), (1, 2, 3, 4), axis=1 )

            query = 'Transformers(name, min_tap, current_tap, max_tap, regulation_step, in_model ) VALUES (?, ?, ?, ?, ?, True);'

            database.insertOrReplaceInto( query, transformers, True )

            nodes = pd.read_csv( fileList[ 1 ]).to_numpy().tolist()

            query = 'Nodes(name, min_voltage, current_voltage, max_voltage, in_model ) VALUES (?, ?, ?, ?, True);'

            database.insertOrReplaceInto( query, nodes )

            query = 'Nodes_generators( generator, node ) VALUES (?, ?);'

            database.insertOrReplaceInto( query, nodesGenerators )

            query = 'Nodes_transformers( transformer, node ) VALUES (?, ?);'

            database.insertOrReplaceInto( query, nodesTransformers )

            baseNodesVoltageChanges = pd.read_csv( fileList[ 4 ] )

            nodesVoltageChangesColumns = baseNodesVoltageChanges.columns.tolist()[2:]

            nodesVoltageChanges = baseNodesVoltageChanges.to_numpy()

            formatedNVC = transformCSVtoSqliteFormat( nodesVoltageChangesColumns, nodesVoltageChanges )
          
            query = 'Nodes_voltage_changes( node, changed_element, changed_element_difference, node_voltage_difference ) VALUES ( ?, ?, ?, ? );'

            database.insertOrReplaceInto( query, formatedNVC )

            baseElementsReactivePowerChanges = pd.read_csv( fileList[ 2 ])

            elementsReactivePowerChangesColumns = baseElementsReactivePowerChanges.columns.tolist()[2:]

            elementsReactivePowerChanges = baseElementsReactivePowerChanges.to_numpy()

            formatedERPC = transformCSVtoSqliteFormat( elementsReactivePowerChangesColumns, elementsReactivePowerChanges )

            query = '''Elements_reactive_power_changes( base_element, changed_element, changed_element_difference, base_element_reactive_power_difference )      
VALUES( ?,?,?,? );'''

            database.insertOrReplaceInto( query, formatedERPC )
       
    except sqlite3.Error as error:

        print( error )

if __name__ == '__main__':

    main()