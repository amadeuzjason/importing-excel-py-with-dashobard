import unittest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from excel_importer import ExcelImporterApp

class TestExcelImporterSimple(unittest.TestCase):
    
    def setUp(self):
        """Set up test data"""
        # Create sample test data
        self.test_data = pd.DataFrame({
            'Nama': ['Alice', 'Bob', 'Charlie', 'David', 'Eva'],
            'Usia': [25, 30, 35, 40, 45],
            'Gaji': [5000000, 6000000, 7000000, 8000000, 9000000],
            'Kota': ['Jakarta', 'Surabaya', 'Bandung', 'Jakarta', 'Surabaya']
        })
    
    def test_sort_numeric_ascending(self):
        """Test sorting numeric column in ascending order"""
        app = ExcelImporterApp.__new__(ExcelImporterApp)
        app.df = self.test_data.copy()
        app.filtered_df = None
        app.current_sort_column = None
        app.current_sort_order = 'asc'
        
        # Sort by Usia ascending
        app.sort_data('asc', 'Usia')
        
        # Check if sorted correctly
        expected_ages = [25, 30, 35, 40, 45]
        actual_ages = app.df['Usia'].tolist()
        
        self.assertEqual(actual_ages, expected_ages, "Numeric ascending sort failed")
    
    def test_sort_numeric_descending(self):
        """Test sorting numeric column in descending order"""
        app = ExcelImporterApp.__new__(ExcelImporterApp)
        app.df = self.test_data.copy()
        app.filtered_df = None
        app.current_sort_column = None
        app.current_sort_order = 'asc'
        
        # Sort by Usia descending
        app.sort_data('desc', 'Usia')
        
        # Check if sorted correctly
        expected_ages = [45, 40, 35, 30, 25]
        actual_ages = app.df['Usia'].tolist()
        
        self.assertEqual(actual_ages, expected_ages, "Numeric descending sort failed")
    
    def test_sort_string_ascending(self):
        """Test sorting string column in ascending order"""
        app = ExcelImporterApp.__new__(ExcelImporterApp)
        app.df = self.test_data.copy()
        app.filtered_df = None
        app.current_sort_column = None
        app.current_sort_order = 'asc'
        
        # Sort by Nama ascending
        app.sort_data('asc', 'Nama')
        
        # Check if sorted correctly
        expected_names = ['Alice', 'Bob', 'Charlie', 'David', 'Eva']
        actual_names = app.df['Nama'].tolist()
        
        self.assertEqual(actual_names, expected_names, "String ascending sort failed")
    
    def test_column_identification(self):
        """Test that column identification works correctly"""
        app = ExcelImporterApp.__new__(ExcelImporterApp)
        app.df = self.test_data.copy()
        app.filtered_df = None
        app.current_sort_column = None
        app.current_sort_order = 'asc'
        
        # Test valid column
        app.sort_treeview('Usia')
        self.assertEqual(app.current_sort_column, 'Usia', "Column identification failed")
    
    def test_sort_order_toggle(self):
        """Test that sort order toggles correctly"""
        app = ExcelImporterApp.__new__(ExcelImporterApp)
        app.df = self.test_data.copy()
        app.filtered_df = None
        app.current_sort_column = None
        app.current_sort_order = 'asc'
        
        # First click - should set to asc
        app.sort_treeview('Usia')
        self.assertEqual(app.current_sort_order, 'asc', "First sort should be ascending")
        
        # Second click - should toggle to desc
        app.sort_treeview('Usia')
        self.assertEqual(app.current_sort_order, 'desc', "Second sort should be descending")
        
        # Third click - should toggle back to asc
        app.sort_treeview('Usia')
        self.assertEqual(app.current_sort_order, 'asc', "Third sort should be ascending again")

if __name__ == '__main__':
    unittest.main()