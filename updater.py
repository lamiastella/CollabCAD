# updater.py

# module to handle/update SQLite database

import sqlite3
import os

# CLASSLESS FUNCTIONS

def pathExists(path):
    """Determines whether a file exists at a certain path"""

    return os.path.exists(path)

# CLASSES

class Updater(object):
    """Module to interface with a SQLite database for update purposes"""

    def __init__(self, database):
        """Constructor for Updater class

        PARAMETERS
        database: database to connect to"""

        self.database = database
        if (not pathExists(self.database)): raise IOError("Invalid path")

    def getConnection(self):
        """Produces a connection to the database"""

        con = sqlite3.connect(self.database)
        return con

    def getTables(self, con=None):
        """Lists all tables that are members of a datbase
        
        OPTIONAL
        con: existing sqlite3 connection
        (recommended for situations in which the connection
        needs to be used after this function runs)"""

        conCreated = False
        if con is None:
            con, conCreated = self.getConnection(), True
        cur, tables = con.cursor(), []
        cur.execute("SELECT name from sqlite_master WHERE type='table'")
        fetch = cur.fetchall()
        if conCreated: 
            try: 
                con.close()
            except: 
                pass
        return [item[0] for item in fetch]

    def tableExists(self, table, con=None):
        """Checks whether a table exists in a database"""

        conCreated = False
        if(con is None):
            con, conCreated = self.getConnection(), True
        result = (table in self.getTables(con=con))
        if conCreated: 
            try: 
                con.close()
            except: 
                pass
        return result

    def getColumns(self, table, error=False, con=None):
        """Lists all columns within a table

        PARAMETERS
        table: table to check

        OPTIONAL
        error: set to True to return IOError if table doesn't exist
        con: provide an existing connection
        (recommended for situations where connection will be
        used after this function call terminates)"""

        conCreated = False
        if con is None:
            con, conCreated = self.getConnection(), True
        if self.tableExists(table, con=con):
            cur, columns, nameIndex = con.cursor(), [], 1
            # nameIndex = index with column names
            cur.execute("PRAGMA table_info({tn})".format(tn=table))
            fetch = cur.fetchall()
            if conCreated: 
                try: 
                    con.close()
                except: 
                    pass
            return [item[nameIndex] for item in fetch]
        elif error:
            raise IOError("Table does not exist")
        else: return []

    def columnExists(self, table, column, con=None):
        """Checks whether a column exists in a table"""

        conCreated = False
        if(con is None):
            con, conCreated = self.getConnection(), True
        if (not self.tableExists(table, con=con)):
            raise IOError("Invalid table!")
        result = (column in self.getColumns(table, con=con))
        if conCreated: 
            try: 
                con.close()
            except: 
                pass
        return result

    def getColumnsForRow(self, table, id_col, ID, error=False, con=None):
        """Lists all columns within a table that exist for a row

        PARAMETERS
        table: table to check
        id_col: id column for row
        ID: id of row

        OPTIONAL
        error: set to True to raise error if table doesn't exist
        con: pre-existing sqlite connection"""

        conCreated = False
        presentCols = []
        if (con is None):
            con, conCreated = self.getConnection(), True
        columns = self.getColumns(table=table, error=error, con=con)
        for column in columns:
            with con:
                cur = con.cursor()
                cur.execute("SELECT * FROM {tn} WHERE {idc} = {id} AND {cn} IS NOT NULL"\
                            .format(tn=table, idc=id_col, id=ID, cn=column))
                if len(cur.fetchall()) > 0:
                    presentCols.append(column)
        if conCreated: 
            try: 
                con.close()
            except: 
                pass
        return presentCols

    def getIndex(self, table, column, error=True, con=None):
        """Returns index of column in a table"""
        
        conCreated = False
        if (con is None):
            con, conCreated = self.getConnection(), True
        if self.columnExists(table, column, con=con):
            result = self.getColumns(table, con=con).index(column)
            if conCreated: 
                try: 
                    con.close()
                except: 
                    pass
            return result
        elif error:
            raise IOError("Column does not exist!")

    def createColumn(self, table, column, 
                     colType="TEXT", error=False,
                     con=None):
        """Creates a new column in a table
        PARAMETERS
        table, column

        OPTIONAL: 
        colType: type of value in column (default is TEXT)
        error (if set to True, raises error if column exists)
        con: existing connection (defaults to None)"""
        
        conCreated = False
        if con is None: 
            con, conCreated = self.getConnection(), True
        if (not self.tableExists(table, con=con)):
            raise IOError("Invalid table!")
        if (not self.columnExists(table, column, con=con)):
            with con:
                cur = con.cursor()
                cur.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct}"\
                            .format(tn=table, cn=column, ct=colType))
            if conCreated: 
                try: 
                    con.close()
                except: 
                    pass
        elif error:
            raise IOError("Column already exists!")

    def createTable(self, table, primaryKey="_id", original=None, 
                    error=False, con=None):
        """Creates a new table in the database
        
        PARAMETERS
        table: name of table to be created

        OPTIONAL
        primaryKey: to generate a primary key
        (name of primary key field to generate- defaults to _id)
        original: another table from which to construct a copy
        error: if set to True, raises error if table exists
        con: pre-existing sqlite connection"""
        
        conCreated = False
        if con is None:
            con, conCreated = self.getConnection(), True
        if (not self.tableExists(table, con=con)):
            with con:
                cur = con.cursor()
                statement = "CREATE TABLE {tn}".format(tn=table)
                if primaryKey != "": 
                    statement +=  " ({pk} integer primary key autoincrement)"\
                                   .format(pk=primaryKey)
                cur.execute(statement)
            if conCreated: 
                try: 
                    con.close()
                except: 
                    pass
        elif error:
            raise IOError("Table already exists!")

    def copyTable(self, newTable, originalTable, foundError=False, 
                  notFoundError=True, con=None, copyContents=True):
        """Create a new table in the database
        based on an existing table
        
        PARAMETERS
        newTable: name of table to be created
        originalTable: name of original table

        OPTIONAL:
        foundError: if set to True, raises error if newTable exists
        notFoundError: if set to True, raises error if originalTable doesn't exist
        (defaults to True)
        con: pre-existing sqlite connection
        copyContents: if set to True, new table copies contents of original
        (defaults to True)"""

        conCreated = False
        if con is None:
            con, conCreated = self.getConnection(), True
        if (not self.tableExists(newTable, con=con)):
            if (self.tableExists(originalTable, con=con)):
                with con:
                    cur = con.cursor()
                    cur.execute("SELECT sql FROM sqlite_master WHERE type='table'\
                                 AND name='{ot}'".format(ot=originalTable))
                    statement = cur.fetchone()[0]
                    command = statement.replace(originalTable, newTable, 1)
                    cur.execute(command)
                    if copyContents:
                        cur.execute("INSERT INTO {nt} SELECT * FROM {ot}"\
                                    .format(nt=newTable, ot=originalTable))
                if conCreated: 
                    try: 
                        con.close()
                    except: 
                        pass
            elif notFoundError:
                raise IOError("Original table does not exist!")
        elif foundError:
            raise IOError("New table already exists!")

    def updateRow(self, data, table, id_col, ID, con=None):
        """Updates a single row in a table 
        based on a dictionary of columns and their values

        PARAMETERS
        data: dictionary of columns with values
        table: table to be modified
        id_col: column through which rows can be identified
        ID: ID of row to be updated

        OPTIONAL
        con: existing sqlite connection"""
        
        if (not self.tableExists(table, con=con)):
            raise IOError("Invalid table!")
        conCreated = False
        if (con is None): 
            con, conCreated = self.getConnection(), True
        for item in data:
            self.createColumn(table, item, con=con)
            with con:
                cur = con.cursor()
                value = str(data[item])
                if "'" in value: value = value.replace("'", "")
                cur.execute("UPDATE {tn} SET {cn} = ('{value}') WHERE {idc} = ({ID})"\
                            .format(tn=table, cn=item, value=value, idc=id_col, ID=ID))
        if conCreated: 
            try: 
                con.close()
            except: 
                pass

    def rowAsDict(self, rowData, colData):
        rowData = [row for row in rowData if row is not None]
        result = dict()
        for i in xrange(len(colData)):
            col = colData[i]
            result[col] = rowData[i]
        return result

    def updateTable(self, table, id_col, fun, minIndex=None, maxIndex=None, con=None, monitor=0):
        """Updates an entire table or a range over the table

        PARAMETERS
        table: table to update
        id_col: id column within table
        fun: function to get a dictionary from a row in the table (to update the row)

        OPTIONAL
        minIndex: minimum index to update (inclusive)
        maxIndex: maximum index to update (inclusive)
        con: pre-existing connection
        monitor: if set to non-zero, prints status on command line every (monitor)th index"""

        if (con is None):
            con, conCreated = self.getConnection(), True
        if (not self.tableExists(table, con=con)): 
            raise IOError("Invalid table!")
        conCreated = False
        id_index = self.getIndex(table, id_col, con=con)
        with con:
            cur = con.cursor()
            if minIndex != None:
                if maxIndex != None:
                    cur.execute("SELECT * FROM {tn} WHERE {idc} >= {min} AND {idc} <= {max}"\
                                   .format(tn=table, idc=id_col, min=minIndex, max=maxIndex))
                else:
                    cur.execute("SELECT * FROM {tn} WHERE {idc} >= {min}"\
                                   .format(tn=table, idc=id_col, min=minIndex))
            else:
                cur.execute("SELECT * FROM {tn}".format(tn=table))
            fetch = cur.fetchall()
            for item in fetch:
                ID = item[id_index]
                columns = self.getColumnsForRow(table, id_col, ID)
                itemDict = self.rowAsDict(item, columns)
                data = fun(itemDict)
                if (monitor != 0 and ID%monitor == 0):
                    print "Updating index", ID, "of table", table, "using", str(fun.__name__)
                self.updateRow(data, table, id_col, ID, con=con)
            if conCreated: 
                try: 
                    con.close()
                except: 
                    pass

    def getRows(self, table, column, col_value, id_col="_id", con=None):
        """Gets rows matching certain criteria

        PARAMETERS
        table: table to check
        column: column to check for values
        col_value: values to check for within column

        OPTIONAL
        con: pre-existing sqlite connection
        id_col: name of ID column (default _id)"""

        conCreated = False
        if (con is None):
            con, conCreated = self.getConnection(), True
        if (not self.tableExists(table, con=con)):
            raise IOError("Invalid table!")
        if (not self.columnExists(table, column, con=con)): 
            raise IOError("Invalid column!")
        id_index = self.getIndex(table, id_col, con=con)
        with con:
            cur = con.cursor()
            cur.execute("SELECT * FROM {tn} WHERE {cn} = {cv}"\
                        .format(tn=table, cn=column, cv=col_value))
        fetch = cur.fetchall()
        if conCreated: con.close()
        return [self.rowAsDict(item, self.getColumnsForRow(table, id_col, item[id_index])) for item in fetch]

    def getDistinctValues(self, table, column, conditions=dict(), con=None):
        """Gets distinct values in a column

        PARAMETERS
        table: table to check
        column: column to check

        OPTIONAL
        conditions: dictionary of requirements in other columns
        con: pre-existing sqlite connection"""

        if (not self.tableExists(table, con=con)):
            raise IOError("Invalid table!")
        if (not self.columnExists(table, column, con=con)): 
            raise IOError("Invalid column!")
        conCreated = False
        if (con is None):
            con, conCreated = self.getConnection(), True
        statement = "SELECT DISTINCT " + column + " FROM " + table
        if (len(conditions) != 0):
            statement += " WHERE "
            firstRequirement = True
            for item in conditions:
                if (not firstRequirement):
                    statement += " AND "
                requirement = conditions[item]
                if (type(requirement) == list):
                    firstIteration = True
                    for value in requirement:
                        if (not firstIteration):
                            statement += " OR "
                        statement += str(item) + " = '" + str(value) + "'"
                else:
                    statement += str(item) + " = '" + str(requirement) + "'"
        with con:
            cur = con.cursor()
            cur.execute(statement)
        fetch = cur.fetchall()
        if conCreated: con.close()
        return [item[0] for item in fetch]

    def getIntersectingValues(self, table, columns, id_col="_id", con=None):
        """Gets values that meet all criteria

        PARAMETERS
        table: table to check
        columns: dictionary of columns with specified values (or lists)

        OPTIONAL
        id_col: id column in table (default _id)
        con: pre-existing sqlite connection"""

        conCreated = False
        if (con is None):
            con, conCreated = self.getConnection(), True
        if (not self.tableExists(table, con=con)):
            raise IOError("Invalid table!")
        for column in columns:
            if (not self.columnExists(table, column, con=con)): 
                raise IOError("Invalid column!")
        id_index = self.getIndex(table, id_col, con=con)
        statement = "SELECT * FROM " + str(table)
        if len(columns) > 0:
            statement +=  " WHERE "
        firstSet = True
        for column in columns:
            if (not firstSet):
                statement += " AND "
            content = columns[column]
            if (type(content) == list):
                statement += "("
                firstIteration = True
                for item in content:
                    if (not firstIteration):
                        statement += " OR "
                    if item is None:
                        statement += str(column) + " IS NULL"
                    else:
                        statement += str(column) + " = '" + str(item) + "'"
                    if (firstIteration):
                        firstIteration = False
                statement += ")"
            else:
                if content is None:
                    statement += str(column) + " IS NULL"
                else:
                    statement += str(column) + " = '" + str(content) + "'"
            firstSet = False
        print "statement", statement
        with con:
            cur = con.cursor()
            cur.execute(statement)
        fetch = cur.fetchall()
        if conCreated:
            con.close()
        return [self.rowAsDict(item, self.getColumnsForRow(table, id_col, item[id_index])) for item in fetch]

    def getFrequency(self, table, columns, id_col="_id", con=None):
        """Gets number of occurrences that meet certain criteria

        PARAMETERS
        table: table to check
        columns: dictionary of columns with specified values (or lists)

        OPTIONAL
        con: pre-existing sqlite connection"""

        return len(self.getIntersectingValues(table, columns, id_col, con))

    def getAssociatedValue(self, table, col1, value, col2, id_col="_id", con=None, error=False):
        """Gets value from col2 associated with value from col1

        PARAMETERS
        table: table to check
        col1: column containing known value
        value: known value
        col2: column containing unknown value

        OPTIONAL
        id_col: id column in table (default _id)
        id_index: location of id column (default 0)
        con: pre-existing sqlite connection
        error: if true, raises error if no associated column exists"""

        conCreated = False
        if (con is None):
            con, conCreated = self.getConnection(), True
        if (not self.tableExists(table, con=con)):
            raise IOError("Invalid table!")
        if (not self.columnExists(table, col1, con=con) or not self.columnExists(table, col2, con=con)): 
            raise IOError("Invalid column!")
        id_index = self.getIndex(table, id_col, con=con)
        cur = con.cursor()
        print "table", table, "column", col1, "value", value
        if value is None:
            print "SELECT * FROM {tn} WHERE {cn} IS NULL".format(tn=table, cn=col1)
            cur.execute("SELECT * FROM {tn} WHERE {cn} IS NULL".format(tn=table, cn=col1))
        else:
            cur.execute("SELECT * FROM {tn} WHERE {cn} = '{cv}'".format(tn=table, cn=col1, cv=value))
        item = cur.fetchone()
        print "item", item
        if item is None: return None
        columns = self.getColumnsForRow(table, id_col, item[id_index])
        item = self.rowAsDict(item, columns)
        if conCreated: con.close()
        print "item", item
        if col2 in item:
            return item[col2]
        elif error:
            raise IOError("Associated column does not exist for this row!")
        else:
            return None

    def addRow(self, table, data, con=None):
        """Adds a row to an existing table

        PARAMETERS
        table: table to add to
        data: dictionary of columns to add to

        OPTIONAL
        con: pre-existing sqlite connection"""

        conCreated = False
        print "data", data
        if (con is None): 
            con, conCreated = self.getConnection(), True
        colList = [str(item) for item in data]
        print "colList", colList
        colString = "','".join(colList)
        valueList = [str(data[item]) for item in data]
        print "valueList", valueList
        for i in xrange(len(valueList)):
            value = valueList[i]
            if "'" in value:
                valueList[i] = value.replace("'", "")
        valueString = "','".join(valueList)
        for item in data:
            # Doesn't create column if it already exists
            self.createColumn(table, item, con=con)
        with con:
            cur = con.cursor()
            print "INSERT INTO {tn} ('{cs}') VALUES ('{vs}')"\
                  .format(tn=table, cs=colString, vs=valueString)
            cur.execute("INSERT INTO {tn} ('{cs}') VALUES ('{vs}')"\
                        .format(tn=table, cs=colString, vs=valueString))
        if conCreated: con.close()