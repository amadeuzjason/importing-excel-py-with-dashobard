import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
import time
from datetime import datetime
import os
import logging
import subprocess
import sys
import webbrowser
import shutil
try:
    import process_export
except Exception:
    process_export = None

# Setup logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='excel_importer.log',
                    filemode='w')

class ExcelImporterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel Data Importer")
        self.root.geometry("1200x800")
        
        self.df = None
        self.filtered_df = None
        self.current_sort_column = None
        self.current_sort_order = "asc"
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # File selection
        ttk.Label(main_frame, text="File Excel:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_path_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.file_path_var, width=80).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5, pady=5)
        
        # Load button
        ttk.Button(main_frame, text="Load File", command=self.load_file).grid(row=1, column=0, columnspan=3, pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to load file")
        ttk.Label(main_frame, textvariable=self.status_var).grid(row=3, column=0, columnspan=3, pady=5)
        
        # Treeview for data display
        self.tree_frame = ttk.Frame(main_frame)
        self.tree_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.rowconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(self.tree_frame, show='headings')
        self.vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Filter controls
        filter_frame = ttk.Frame(main_frame)
        filter_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(filter_frame, text="Filter by:").grid(row=0, column=0, sticky=tk.W)
        self.filter_column_var = tk.StringVar()
        self.filter_column_combo = ttk.Combobox(filter_frame, textvariable=self.filter_column_var, state='readonly')
        self.filter_column_combo.grid(row=0, column=1, padx=5)
        
        self.filter_value_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.filter_value_var, width=20).grid(row=0, column=2, padx=5)
        
        ttk.Button(filter_frame, text="Apply Filter", command=self.apply_filter).grid(row=0, column=3, padx=5)
        ttk.Button(filter_frame, text="Clear Filter", command=self.clear_filter).grid(row=0, column=4, padx=5)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Sort Ascending", command=lambda: self.sort_data('asc')).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Sort Descending", command=lambda: self.sort_data('desc')).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Validate Data", command=self.validate_data).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Export to Excel", command=self.export_data).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="Show Statistics", command=self.show_statistics).grid(row=0, column=4, padx=5)
        
        # Bind events
        self.tree.bind('<Button-1>', self.on_tree_click)
        self.filter_value_var.trace('w', self.on_filter_change)
        
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
    
    def load_file(self):
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showerror("Error", "Please select a file first")
            return
        
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "File does not exist")
            return
        
        self.status_var.set("Loading file...")
        self.progress.start(10)
        
        # Run loading in separate thread
        threading.Thread(target=self._load_file_thread, daemon=True).start()
    
    def _load_file_thread(self):
        try:
            file_path = self.file_path_var.get()
            self.current_file = file_path
            
            # Read Excel file
            self.df = pd.read_excel(file_path, engine='openpyxl')
            
            # Update UI in main thread
            self.root.after(0, self._file_loaded_successfully)
            
        except Exception as e:
            self.root.after(0, lambda: self._file_load_error(str(e)))
    
    def _file_loaded_successfully(self):
        self.progress.stop()
        self.status_var.set(f"File loaded successfully: {len(self.df)} rows, {len(self.df.columns)} columns")
        
        # Update filter column combo
        self.filter_column_combo['values'] = self.df.columns.tolist()
        if self.df.columns.any():
            self.filter_column_var.set(self.df.columns[0])
        
        # Display data
        self.display_data()
        
        messagebox.showinfo("Success", f"File loaded successfully!\nRows: {len(self.df)}\nColumns: {len(self.df.columns)}")
    
    def _file_load_error(self, error_msg):
        self.progress.stop()
        self.status_var.set("Error loading file")
        messagebox.showerror("Error", f"Failed to load file:\n{error_msg}")
    
    def display_data(self, data=None):
        if data is None:
            data = self.df
        
        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree['columns'] = []
        
        if data is None or data.empty:
            return
        
        # Set up columns
        columns = data.columns.tolist()
        self.tree['columns'] = columns
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, minwidth=50)
        
        # Add data (limited to 1000 rows for performance)
        display_data = data.head(1000) if len(data) > 1000 else data
        
        for _, row in display_data.iterrows():
            values = [str(row[col]) if pd.notna(row[col]) else "" for col in columns]
            self.tree.insert("", "end", values=values)
    
    def sort_treeview(self, column):
        if self.df is None:
            logging.warning("Attempted to sort but no data loaded")
            return
        
        logging.debug(f"Sorting column: {column}, current sort column: {self.current_sort_column}")
        
        if self.current_sort_column == column:
            self.current_sort_order = 'desc' if self.current_sort_order == 'asc' else 'asc'
        else:
            self.current_sort_column = column
            self.current_sort_order = 'asc'
        
        logging.debug(f"New sort order: {self.current_sort_order} for column: {column}")
        self.sort_data(self.current_sort_order, column)
    
    def sort_data(self, order='asc', column=None):
        if self.df is None:
            return
        
        if column is None:
            # If no column specified, use the first column
            if len(self.df.columns) > 0:
                column = self.df.columns[0]
            else:
                messagebox.showinfo("Info", "No columns available for sorting")
                return
        
        try:
            data_to_sort = self.filtered_df if self.filtered_df is not None else self.df
            
            if column not in data_to_sort.columns:
                logging.error(f"Column '{column}' not found in data. Available columns: {list(data_to_sort.columns)}")
                messagebox.showerror("Error", f"Column '{column}' not found in data")
                return
            
            # Handle different data types for sorting
            if pd.api.types.is_numeric_dtype(data_to_sort[column]):
                sorted_df = data_to_sort.sort_values(by=column, ascending=(order == 'asc'))
            elif pd.api.types.is_datetime64_any_dtype(data_to_sort[column]):
                sorted_df = data_to_sort.sort_values(by=column, ascending=(order == 'asc'))
            else:
                sorted_df = data_to_sort.sort_values(by=column, ascending=(order == 'asc'), key=lambda x: x.astype(str).str.lower())
            
            if self.filtered_df is not None:
                self.filtered_df = sorted_df
            else:
                self.df = sorted_df
            
            self.display_data(sorted_df)
            self.status_var.set(f"Sorted by {column} ({order})")
            
        except Exception as e:
            messagebox.showerror("Error", f"Sorting error: {str(e)}")
    
    def apply_filter(self):
        if self.df is None:
            return
        
        column = self.filter_column_var.get()
        value = self.filter_value_var.get().strip()
        
        if not column or not value:
            messagebox.showinfo("Info", "Please select column and enter filter value")
            return
        
        try:
            if column not in self.df.columns:
                messagebox.showerror("Error", f"Column '{column}' not found in data")
                return
            
            # Handle different filter types with proper NaN handling
            if pd.api.types.is_numeric_dtype(self.df[column]):
                # For numeric columns (including large IDs like UniqueId, CID),
                # use string-based contains matching so users can search by
                # full value or partial digits (prefix/substring).
                if value.lower() in ['null', 'nan', 'na', '']:
                    self.filtered_df = self.df[pd.isna(self.df[column])]
                else:
                    col_as_str = self.df[column].astype(str)
                    self.filtered_df = self.df[
                        col_as_str.str.contains(value, case=False, na=False)
                    ]
            
            elif pd.api.types.is_datetime64_any_dtype(self.df[column]):
                try:
                    date_value = pd.to_datetime(value)
                    self.filtered_df = self.df[
                        (self.df[column] == date_value) | 
                        (pd.isna(self.df[column]) & (value.lower() in ['null', 'nan', 'na', '']))
                    ]
                except ValueError:
                    # Try partial match for dates or NaN values
                    if value.lower() in ['null', 'nan', 'na', '']:
                        self.filtered_df = self.df[pd.isna(self.df[column])]
                    else:
                        # Try partial string matching for date strings
                        self.filtered_df = self.df[
                            self.df[column].astype(str).str.contains(value, case=False, na=False)
                        ]
            
            else:
                # Text filter with proper NaN handling
                if value.lower() in ['null', 'nan', 'na']:
                    self.filtered_df = self.df[pd.isna(self.df[column])]
                else:
                    # Use fillna to handle NaN values in string columns
                    self.filtered_df = self.df[
                        self.df[column].astype(str).str.contains(value, case=False, na=False)
                    ]
            
            if len(self.filtered_df) == 0:
                self.status_var.set(f"No results found for '{value}' in column '{column}'")
                messagebox.showinfo("Filter Results", f"No data found matching '{value}' in column '{column}'")
            else:
                self.display_data(self.filtered_df)
                self.status_var.set(f"Filter applied: {column} contains '{value}' - {len(self.filtered_df)} rows found")
            
        except Exception as e:
            messagebox.showerror("Error", f"Filter error: {str(e)}")
            print(f"Filter error details: {e}")
    
    def clear_filter(self):
        self.filtered_df = None
        self.filter_value_var.set("")
        if self.df is not None:
            self.display_data(self.df)
            self.status_var.set("Filter cleared")
    
    def on_filter_change(self, *args):
        # Real-time filtering could be implemented here
        pass
    
    def validate_data(self):
        if self.df is None:
            return
        
        validation_results = []
        
        # Check for missing values
        missing_values = self.df.isnull().sum()
        for col, count in missing_values.items():
            if count > 0:
                validation_results.append(f"{col}: {count} missing values")
        
        # Check data types consistency
        for col in self.df.columns:
            unique_types = self.df[col].apply(type).nunique()
            if unique_types > 1:
                validation_results.append(f"{col}: Mixed data types detected")
        
        # Show results
        if validation_results:
            result_text = "Validation Results:\n\n" + "\n".join(validation_results)
            messagebox.showwarning("Validation Results", result_text)
        else:
            messagebox.showinfo("Validation Results", "No validation issues found!")
    
    def export_data(self):
        if self.df is None:
            return
        data_to_export = self.filtered_df if self.filtered_df is not None else self.df
        if data_to_export.empty:
            messagebox.showinfo("Info", "No data to export")
            return
        if self.current_sort_column and self.current_sort_column in data_to_export.columns:
            data_to_export = data_to_export.sort_values(
                by=self.current_sort_column,
                ascending=(self.current_sort_order == 'asc')
            )
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Save Export File"
        )
        if not file_path:
            return
        try:
            self._write_excel_with_metadata(data_to_export, file_path)
            self.merge_to_dashboard_excel(data_to_export)
            merged_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "merged_current.xlsx")
            if process_export is not None:
                try:
                    process_export.process(file_path)
                    logging.info(f"Merge pipeline updated from: {file_path}")
                except Exception as e:
                    logging.error(f"Merge pipeline failed: {e}")
            else:
                logging.warning("process_export module not available, skipping merge pipeline")
            messagebox.showinfo("Success", f"Data exported successfully to {file_path}\n\nRows exported: {len(data_to_export)}\nSort: {self.current_sort_column or 'None'} {self.current_sort_order or ''}\nFilter: {self.filter_column_var.get() or 'None'} = {self.filter_value_var.get() or 'None'}")
            self.status_var.set(f"Data exported: {len(data_to_export)} rows with current sort/filter")
            dashboard_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_export.xlsx")
            target_path = merged_path if os.path.exists(merged_path) else dashboard_path
            self.launch_web_dashboard(target_path)
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
            print(f"Export error details: {e}")
    
    def _write_excel_with_metadata(self, df_to_save, path):
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            df_to_save.to_excel(writer, sheet_name='Data', index=False)
            metadata = {
                'Export Information': [
                    f'Export Date: {pd.Timestamp.now()}',
                    f'Source File: {getattr(self, "current_file", "Unknown")}',
                    f'Total Rows Exported: {len(df_to_save)}',
                    f'Filter Applied: {self.filter_value_var.get() if self.filter_value_var.get() else "None"}',
                    f'Filter Column: {self.filter_column_var.get() if self.filter_column_var.get() else "None"}',
                    f'Sort Column: {self.current_sort_column if self.current_sort_column else "None"}',
                    f'Sort Order: {self.current_sort_order if self.current_sort_order else "None"}'
                ]
            }
            pd.DataFrame(metadata).to_excel(writer, sheet_name='Metadata', index=False)
    
    def merge_to_dashboard_excel(self, df_new):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        export_dir = os.path.join(base_dir, "export")
        backup_dir = os.path.join(export_dir, "backup")
        
        # Ensure target directories exist
        os.makedirs(backup_dir, exist_ok=True)
        
        dashboard_path = os.path.join(export_dir, "dashboard_export.xlsx")
        
        if df_new is None or df_new.empty:
            logging.info("merge_to_dashboard_excel: no data to merge")
            return
        
        df_new = df_new.copy()
        ts = datetime.utcnow().isoformat()
        user_id = os.environ.get("EXPORT_USER") or os.environ.get("USERNAME") or "desktop"
        
        # SYNC ENGINE INTEGRATION
        sync_results = None
        if process_export is not None:
            try:
                conn = process_export.connect_db()
                # Ensure schema is up to date
                process_export.ensure_schema(conn, list(df_new.columns))
                
                # Perform field-level synchronization
                sync_results = process_export.detect_and_sync_changes(conn, df_new, source_file=getattr(self, "current_file", "desktop"))
                conn.close()
                
                # Show notification if modifications occurred
                if sync_results["modifications"]:
                    change_count = len(sync_results["modifications"])
                    msg = f"SYNC ALERT: {change_count} field modifications detected and synchronized.\n\n"
                    for mod in sync_results["modifications"][:5]: # Show first 5
                        msg += f"- [{mod['nop']}] {mod['field']}: {mod['old']} -> {mod['new']}\n"
                    if change_count > 5:
                        msg += f"... and {change_count - 5} more."
                    
                    messagebox.showwarning("Data Sync Alert", msg)
                    logging.info(f"SYNC: {change_count} modifications detected during export.")
                
                # If everything was a duplicate/unchanged and nothing new was added, we can stop or continue to update Excel
                if sync_results["new_records"] == 0 and sync_results["updated_records"] == 0:
                    logging.info("SYNC: No new or updated records to sync to Excel.")
            except Exception as e:
                logging.error(f"Sync Engine failed: {e}")
                messagebox.showerror("Sync Error", f"Automated synchronization failed: {e}")

        # Update the physical Excel file for dashboard fallback
        if os.path.exists(dashboard_path):
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"dashboard_export_backup_{timestamp}.xlsx"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            try:
                shutil.copy2(dashboard_path, backup_path)
            except Exception as e:
                logging.error(f"Failed to create backup: {e}")
            
            try:
                # Load latest data from DB if sync was successful, otherwise fallback to Excel merge
                if sync_results:
                    conn = process_export.connect_db()
                    combined = process_export.load_current(conn)
                    conn.close()
                else:
                    excel_obj = pd.read_excel(dashboard_path, sheet_name=None)
                    df_old = excel_obj.get("Data", next(iter(excel_obj.values()))) if isinstance(excel_obj, dict) else excel_obj
                    combined = pd.concat([df_old, df_new], ignore_index=True).drop_duplicates(subset=["NOP"], keep="last")
            except Exception as e:
                logging.error(f"Error reading existing dashboard file: {e}")
                combined = df_new
        else:
            combined = df_new
            
        try:
            with pd.ExcelWriter(dashboard_path, engine="openpyxl") as writer:
                combined.to_excel(writer, index=False, sheet_name="Data")
            
            logging.info(f"Dashboard export updated: {dashboard_path}")
            if not sync_results or (sync_results["new_records"] > 0 or sync_results["updated_records"] > 0):
                messagebox.showinfo("Export Berhasil", f"Data berhasil diexport dan disinkronisasi.\nTotal data sekarang: {len(combined)}")
        except Exception as e:
            logging.error(f"Failed to save dashboard export: {e}")
            messagebox.showerror("Error Export", f"Gagal menyimpan file export: {e}")


    
    def launch_web_dashboard(self, export_path):
        try:
            env = os.environ.copy()
            # Pastikan web_app membaca file export dashboard yang benar
            env["EXCEL_DASHBOARD_FILE"] = os.path.abspath(export_path)
            env.setdefault("DASHBOARD_PORT", "5000")
            python_executable = sys.executable
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_app.py")
            subprocess.Popen([python_executable, script_path], env=env)
            url = f"http://127.0.0.1:{env['DASHBOARD_PORT']}/"
            webbrowser.open(url)
        except Exception as e:
            logging.error(f"Failed to launch web dashboard: {e}")
    
    def show_statistics(self):
        if self.df is None:
            return
        
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Data Statistics")
        stats_window.geometry("600x400")
        
        text_area = ScrolledText(stats_window, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        stats_text = f"Data Statistics\n{'='*50}\n"
        stats_text += f"Total rows: {len(self.df)}\n"
        stats_text += f"Total columns: {len(self.df.columns)}\n\n"
        
        stats_text += f"Column Information:\n{'='*50}\n"
        for col in self.df.columns:
            stats_text += f"{col}: {self.df[col].dtype}\n"
            stats_text += f"  Missing values: {self.df[col].isnull().sum()}\n"
            if pd.api.types.is_numeric_dtype(self.df[col]):
                stats_text += f"  Min: {self.df[col].min():.2f}\n"
                stats_text += f"  Max: {self.df[col].max():.2f}\n"
                stats_text += f"  Mean: {self.df[col].mean():.2f}\n"
            stats_text += "\n"
        
        text_area.insert(tk.END, stats_text)
        text_area.config(state=tk.DISABLED)
    
    def on_tree_click(self, event):
        # Handle treeview clicks for sorting
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            # Get the actual column ID that was clicked
            column_id = self.tree.identify_column(event.x)
            
            # Convert column ID to index (e.g., '#1' -> 0)
            try:
                col_index = int(column_id.replace('#', '')) - 1
                
                # Safety check to ensure index is within bounds
                if 0 <= col_index < len(self.tree['columns']):
                    col_name = self.tree['columns'][col_index]
                    self.sort_treeview(col_name)
                    
            except (ValueError, IndexError) as e:
                print(f"Error identifying column: {e}")
                return

def main():
    root = tk.Tk()
    app = ExcelImporterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
