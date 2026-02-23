import unittest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from excel_importer import ExcelImporterApp

class TestExcelImporter(unittest.TestCase):
    
    def setUp(self):
        """Set up test data"""
        # Create sample test data
        self.test_data = pd.DataFrame({
            'Nama': ['Alice', 'Bob', 'Charlie', 'David', 'Eva'],
            'Usia': [25, 30, 35, 40, 45],
            'Gaji': [5000000, 6000000, 7000000, 8000000, 9000000],
            'Tanggal': [
                datetime(2023, 1, 1),
                datetime(2023, 2, 1),
                datetime(2023, 3, 1),
                datetime(2023, 4, 1),
                datetime(2023, 5, 1)
            ],
            'Kota': ['Jakarta', 'Surabaya', 'Bandung', 'Jakarta', 'Surabaya']
        })
        
        # Create test data with NaN values
        self.test_data_with_nan = pd.DataFrame({
            'Nama': ['Alice', 'Bob', 'Charlie', 'David', 'Eva'],
            'Usia': [25, 30, np.nan, 40, 45],
            'Gaji': [5000000, np.nan, 7000000, 8000000, 9000000],
            'Kota': ['Jakarta', 'Surabaya', 'Bandung', np.nan, 'Surabaya']
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
        
        # Sort by Nama ascending
        app.sort_data('asc', 'Nama')
        
        # Check if sorted correctly
        expected_names = ['Alice', 'Bob', 'Charlie', 'David', 'Eva']
        actual_names = app.df['Nama'].tolist()
        
        self.assertEqual(actual_names, expected_names, "String ascending sort failed")
    
    def test_filter_numeric_exact_match(self):
        """Test filtering numeric column with exact match"""
        app = ExcelImporterApp.__new__(ExcelImporterApp)
        app.df = self.test_data.copy()
        app.filter_column_var = type('', (), {'get': lambda: 'Usia'})()
        app.filter_value_var = type('', (), {'get': lambda: '30'})()
        
        # Apply filter
        app.apply_filter()
        
        # Should find exactly one row
        self.assertEqual(len(app.filtered_df), 1, "Numeric exact filter failed")
        self.assertEqual(app.filtered_df.iloc[0]['Usia'], 30, "Wrong numeric filter result")
    
    def test_filter_string_contains(self):
        """Test filtering string column with contains"""
        app = ExcelImporterApp.__new__(ExcelImporterApp)
        app.df = self.test_data.copy()
        app.filter_column_var = type('', (), {'get': lambda: 'Kota'})()
        app.filter_value_var = type('', (), {'get': lambda: 'Jakarta'})()
        
        # Apply filter
        app.apply_filter()
        
        # Should find rows containing 'Jakarta'
        self.assertEqual(len(app.filtered_df), 2, "String contains filter failed")
        self.assertTrue(all('Jakarta' in city for city in app.filtered_df['Kota']), "Wrong string filter result")
    
    def test_filter_nan_values(self):
        """Test filtering for NaN values"""
        app = ExcelImporterApp.__new__(ExcelImporterApp)
        app.df = self.test_data_with_nan.copy()
        app.filter_column_var = type('', (), {'get': lambda: 'Usia'})()
        app.filter_value_var = type('', (), {'get': lambda: 'nan'})()
        
        # Apply filter for NaN values
        app.apply_filter()
        
        # Should find one row with NaN in Usia
        self.assertEqual(len(app.filtered_df), 1, "NaN filter failed")
        self.assertTrue(pd.isna(app.filtered_df.iloc[0]['Usia']), "Wrong NaN filter result")
    
    def test_filter_date_column(self):
        """Test filtering date column"""
        app = ExcelImporterApp.__new__(ExcelImporterApp)
        app.df = self.test_data.copy()
        app.filter_column_var = type('', (), {'get': lambda: 'Tanggal'})()
        app.filter_value_var = type('', (), {'get': lambda: '2023-01-01'})()
        
        # Apply filter
        app.apply_filter()
        
        # Should find one row with exact date match
        self.assertEqual(len(app.filtered_df), 1, "Date filter failed")
        self.assertEqual(app.filtered_df.iloc[0]['Tanggal'], datetime(2023, 1, 1), "Wrong date filter result")
    
    def test_column_identification(self):
        """Test that column identification works correctly"""
        app = ExcelImporterApp.__new__(ExcelImporterApp)
        app.df = self.test_data.copy()
        
        # Test valid column
        app.current_sort_column = None
        app.sort_treeview('Usia')
        self.assertEqual(app.current_sort_column, 'Usia', "Column identification failed")
        
        # Test invalid column
        app.current_sort_column = None
        try:
            app.sort_treeview('InvalidColumn')
            self.fail("Should have failed for invalid column")
        except:
            pass  # Expected behavior
    
    def test_sort_order_toggle(self):
        """Test that sort order toggles correctly"""
        app = ExcelImporterApp.__new__(ExcelImporterApp)
        app.df = self.test_data.copy()
        
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