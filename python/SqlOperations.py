class SqlOperations:

    def __init__( self, connection ):
        
        self.connection = connection
        self.cursor = connection.cursor()

    def insertOrReplaceInto( self, query, inputList, excludeLastColumn=False ):

        tmpList = inputList[:]

        for row in tmpList:

            if excludeLastColumn: 

                tmp = row.pop()

            self.cursor.execute( 'INSERT OR REPLACE INTO ' + query, row )

    def executeScript( self, query ):

        self.cursor.executescript( query )
