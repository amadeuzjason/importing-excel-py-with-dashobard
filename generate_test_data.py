import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def generate_sample_data(num_rows=100000):
    """Generate sample test data with various data types"""
    
    print(f"Generating {num_rows} rows of sample data...")
    
    # Generate sample data
    data = {
        'ID': range(1, num_rows + 1),
        'Nama': [f'Customer_{i:06d}' for i in range(1, num_rows + 1)],
        'Umur': np.random.randint(18, 80, num_rows),
        'Gaji': np.random.normal(5000000, 2000000, num_rows).round(2),
        'Tanggal_Registrasi': [datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1000)) for _ in range(num_rows)],
        'Kota': np.random.choice(['Jakarta', 'Surabaya', 'Bandung', 'Medan', 'Makassar', 'Yogyakarta'], num_rows),
        'Status': np.random.choice(['Aktif', 'Non-Aktif', 'Pending', 'Blokir'], num_rows, p=[0.7, 0.1, 0.15, 0.05]),
        'Rating': np.random.uniform(1, 5, num_rows).round(2),
        'Jumlah_Transaksi': np.random.poisson(5, num_rows),
        'Terakhir_Login': [datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365)) for _ in range(num_rows)]
    }
    
    # Add some missing values for testing
    for col in ['Umur', 'Gaji', 'Rating']:
        mask = np.random.choice([True, False], num_rows, p=[0.05, 0.95])
        data[col] = [None if mask[i] else data[col][i] for i in range(num_rows)]
    
    df = pd.DataFrame(data)
    
    # Create different test files
    
    # 1. Complete data
    df.to_excel('sample_data_complete.xlsx', index=False, engine='openpyxl')
    print("Created: sample_data_complete.xlsx")
    
    # 2. Data with some errors
    df_error = df.copy()
    # Add some mixed data types
    df_error.loc[df_error.sample(1000).index, 'Umur'] = 'invalid_age'
    df_error.loc[df_error.sample(500).index, 'Gaji'] = 'not_a_number'
    df_error.to_excel('sample_data_with_errors.xlsx', index=False, engine='openpyxl')
    print("Created: sample_data_with_errors.xlsx")
    
    # 3. Small sample for quick testing
    df_small = df.head(1000)
    df_small.to_excel('sample_data_small.xlsx', index=False, engine='openpyxl')
    print("Created: sample_data_small.xlsx")
    
    # 4. Large file for performance testing
    if num_rows > 50000:
        df_large = df.copy()
        df_large.to_excel('sample_data_large.xlsx', index=False, engine='openpyxl')
        print("Created: sample_data_large.xlsx")
        
        # Check file size
        file_size = os.path.getsize('sample_data_large.xlsx') / (1024 * 1024)
        print(f"Large file size: {file_size:.2f} MB")
    
    print("\nSample data generation completed!")
    print("Files created:")
    print("- sample_data_complete.xlsx (Complete sample data)")
    print("- sample_data_with_errors.xlsx (Data with validation errors)")
    print("- sample_data_small.xlsx (Small dataset for quick testing)")
    if num_rows > 50000:
        print("- sample_data_large.xlsx (Large dataset for performance testing)")

def generate_corrupted_file():
    """Generate a corrupted Excel file for testing error handling"""
    
    print("Creating corrupted test file...")
    
    # Create a simple dataframe
    df = pd.DataFrame({
        'Test': ['Data1', 'Data2', 'Data3'],
        'Value': [1, 2, 3]
    })
    
    # Save normally first
    df.to_excel('corrupted_test.xlsx', index=False, engine='openpyxl')
    
    # Corrupt the file by writing random bytes
    try:
        with open('corrupted_test.xlsx', 'ab') as f:
            f.write(os.urandom(100))  # Add random bytes to corrupt
        print("Created: corrupted_test.xlsx (for error handling testing)")
    except:
        print("Could not create corrupted file")

if __name__ == "__main__":
    # Generate sample data
    generate_sample_data(100000)
    
    # Generate corrupted file for error testing
    generate_corrupted_file()
    
    print("\nAll test files have been generated!")
    print("\nYou can now run the Excel Importer application using:")
    print("python excel_importer.py")