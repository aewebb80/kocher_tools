import os
import sys
import sqlite3
import unittest
import filecmp
import shutil
import tempfile
import io
import string
import random

from kocher_tools.database import *
from tests.functions import checkTable, checkColumn, checkValue

# Run tests for database.py
class test_database (unittest.TestCase):

	@classmethod
	def setUpClass(cls):

		# Create a temporary directory
		cls.test_dir = tempfile.mkdtemp()

		# Assign the filename of the database
		cls.database = os.path.join(cls.test_dir, 'testDB.sqlite')

	@classmethod
	def tearDownClass(cls):

		# Remove the test directory after the tests
		shutil.rmtree(cls.test_dir)

	# Check valueMarksStr
	def test_01_valueMarksStr (self):

		# Run Tests
		self.assertEqual(valueMarksStr(['Test-1']), '?')
		self.assertEqual(valueMarksStr(['Test-1', '"Test 2"']), '?, ?')
		self.assertEqual(valueMarksStr(['Test-1', '"Test 2"', 'Test3']), '?, ?, ?')

	# Check quoteStr
	def test_02_quoteStr (self):
		
		# Run Tests
		self.assertEqual(quoteStr('Test-1'), '"Test-1"')
		self.assertEqual(quoteStr('"Test 2"'), '"Test 2"')
		self.assertEqual(quoteStr('Test3'), 'Test3')

	# Check quoteField
	def test_03_quoteField (self):
		
		# Run Tests
		self.assertEqual(quoteField('Test-1'), '"Test-1"')
		self.assertEqual(quoteField('"Test 2"'), '"Test 2"')
		self.assertEqual(quoteField('Test3'), 'Test3')
		self.assertEqual(quoteField('Test-1.Unique ID'),'"Test-1"."Unique ID"')
		self.assertEqual(quoteField('Test-1.Species'), '"Test-1".Species')
		self.assertEqual(quoteField('Test-1.SubTest3'), '"Test-1".SubTest3')
		self.assertEqual(quoteField('Test. 4', split_by_dot = False), '"Test. 4"')

	# Check quoteFields
	def test_04_quoteFields (self):
		
		# Run Tests
		self.assertEqual(quoteFields(['Test-1', "Test 2"]), ['"Test-1"', '"Test 2"'])
		self.assertEqual(quoteFields(['Test-1', "Test 2", 'Test3', 'Test. 4'], split_by_dot = False), ['"Test-1"', '"Test 2"', 'Test3', '"Test. 4"'])

	# Check returnSetExpression
	def test_05_returnSetExpression (self):
		
		# Run Tests
		self.assertEqual(returnSetExpression({'Test-1': 1, '"Test 2"': 2, 'Test3': 3}), '"Test-1" = ?, "Test 2" = ?, Test3 = ?')

	# Check returnSelectionDict
	def test_06_returnSelectionDict (self):
		
		# Run Tests
		self.assertEqual(returnSelectionDict({'IN': {'Test-1':['Unique ID']}}), '"Test-1" IN (?)')
		self.assertEqual(returnSelectionDict({'NOT IN': {'Test-1':['Unique ID', 'Species']}}), '"Test-1" NOT IN (?, ?)')
		self.assertEqual(returnSelectionDict({'IN': {'Test-1':['Unique ID'], '"Test 2"':['Species']}}), '"Test-1" IN (?) AND "Test 2" IN (?)')
		self.assertEqual(returnSelectionDict({'LIKE': {'Test-1':['Unique ID']}}), '"Test-1" LIKE ?')
		self.assertEqual(returnSelectionDict({'NOT LIKE': {'Test-1':['Unique ID', 'Species']}}), '("Test-1" NOT LIKE ? OR "Test-1" NOT LIKE ?)')

	# Check returnSelectionValues
	def test_07_returnSelectionValues (self):
		
		# Run Tests
		self.assertEqual(returnSelectionValues({'IN': {'Test-1':['Unique ID']}}), ['"Unique ID"'])
		self.assertEqual(returnSelectionValues({'NOT IN': {'Test-1':['Unique ID', 'Species']}}), ['"Unique ID"', 'Species'])

	# Check innerJoinTables
	def test_08_innerJoinTables (self):
		
		# Run Tests
		self.assertEqual(innerJoinTables(['Table1', 'Table2'], ['Unique ID']), 'Table1 INNER JOIN Table2 ON Table1."Unique ID" = Table2."Unique ID"')
		self.assertEqual(innerJoinTables(['Table1', {'Table2':['Table2', 'Table3']}], [{'Unique ID':['Species']}]), 'Table1 INNER JOIN (Table2 INNER JOIN Table3 ON Table2.Species = Table3.Species) Table2 ON Table1."Unique ID" = Table2."Unique ID"')

	# Check createTable
	def test_09_createTable (self):

		# Create the database
		createTable(self.database, 'Table1', '"Unique ID" text, "Last Modified (Table1)" text, "Entry Created (Table1)" text')
		createTable(self.database, 'Table2', '"Unique ID" text, Species text, "Last Modified (Table2)" text, "Entry Created (Table2)" text')
		createTable(self.database, 'Table3', 'Species text, "Last Modified (Table3)" text, "Entry Created (Table3)" text')

		# Check the tables exist
		self.assertTrue(checkTable(self.database, 'Table1'))
		self.assertTrue(checkTable(self.database, 'Table2'))
		self.assertTrue(checkTable(self.database, 'Table3'))

		# Check the columns exist
		self.assertTrue(checkColumn(self.database, 'Table1', "Unique ID"))
		self.assertTrue(checkColumn(self.database, 'Table1', "Last Modified (Table1)"))
		self.assertTrue(checkColumn(self.database, 'Table1', "Entry Created (Table1)"))
		self.assertTrue(checkColumn(self.database, 'Table2', "Unique ID"))
		self.assertTrue(checkColumn(self.database, 'Table2', 'Species'))
		self.assertTrue(checkColumn(self.database, 'Table2', "Last Modified (Table2)"))
		self.assertTrue(checkColumn(self.database, 'Table2', "Entry Created (Table2)"))	  
		self.assertTrue(checkColumn(self.database, 'Table3', 'Species'))
		self.assertTrue(checkColumn(self.database, 'Table3', "Last Modified (Table3)"))
		self.assertTrue(checkColumn(self.database, 'Table3', "Entry Created (Table3)"))

	# Check insertValues
	def test_10_insertValues (self):

		# Insert values into the database
		insertValues(self.database, 'Table1', ["Unique ID"], ['Value1'])
		insertValues(self.database, 'Table2', ["Unique ID", 'Species'], ['Value1', 'Value2'])
		insertValues(self.database, 'Table3', ['Species'], ['Value2'])

		# Check that the values were correctly inserted 
		self.assertTrue(checkValue(self.database, 'Table1', '"Unique ID"', 'Value1'))
		self.assertTrue(checkValue(self.database, 'Table2', '"Unique ID"', 'Value1'))
		self.assertTrue(checkValue(self.database, 'Table2', 'Species', 'Value2'))
		self.assertTrue(checkValue(self.database, 'Table3', 'Species', 'Value2'))

	# Check updateValues
	def test_11_updateValues (self):

		# Update values in the database withing having to join tables
		updateValues(self.database, 'Table1', {'IN': {'"Unique ID"':['Value1']}}, {'"Unique ID"': 'Updated1'})
		updateValues(self.database, 'Table2', {'IN': {'"Unique ID"':['Value1']}}, {'"Unique ID"': 'Updated1'})

		# Check that the values were correctly inserted 
		self.assertTrue(checkValue(self.database, 'Table1', '"Unique ID"', 'Updated1'))
		self.assertTrue(checkValue(self.database, 'Table2', '"Unique ID"', 'Updated1'))

		# Update value in the database with joined tables
		updateValues(self.database, 'Table1', {'IN':{'Table1."Unique ID"': ['Updated1'], 'Table2.Species': ['Value2']}}, {'"Unique ID"': 'Updated2'}, update_table_column = "Unique ID", tables_to_join = ['Table1', 'Table2'], join_table_columns = ['"Unique ID"'])
		updateValues(self.database, 'Table2', {'IN': {'"Unique ID"':['Updated1']}}, {'"Unique ID"': 'Updated2'})

		# Check that the value were correctly inserted 
		self.assertTrue(checkValue(self.database, 'Table1', '"Unique ID"', 'Updated2'))
		self.assertTrue(checkValue(self.database, 'Table2', '"Unique ID"', 'Updated2'))

	# Check retrieveValues
	def test_12_retrieveValues (self):

		# Retrieve values from the database
		retrieved_entries = retrieveValues(self.database, ['Table1', 'Table2'], {}, ['Table1."Unique ID"', 'Table2.Species'], join_table_columns = ['"Unique ID"'])

		# Check that the value were correctly retrieved
		self.assertTrue(len(retrieved_entries) == 1)
		self.assertTrue(len(retrieved_entries[0]) == 2)
		self.assertTrue(list(retrieved_entries[0].keys()) == ['Unique ID', 'Species'])
		self.assertTrue(list(retrieved_entries[0]) == ['Updated2', 'Value2'])

if __name__ == "__main__":
	unittest.main(verbosity = 2)