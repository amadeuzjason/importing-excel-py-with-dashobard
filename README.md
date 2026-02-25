# Panduan Penggunaan Aplikasi Excel Importer

## 📋 Deskripsi Aplikasi
Aplikasi Excel Importer adalah program Python yang dirancang untuk mengimpor, mengolah, dan menganalisis data dari file Excel. Aplikasi ini memiliki antarmuka yang user-friendly dan mendukung operasi data dalam skala besar (hingga 100.000+ baris).

## 🚀 Fitur Utama
- **Import File Excel**: Membaca file .xlsx dan .xls
- **Sorting Data**: Pengurutan ascending/descending untuk semua kolom
- **Filtering Data**: Penyaringan berdasarkan teks, angka, dan tanggal
- **Validasi Data**: Deteksi missing values dan pemeriksaan tipe data
- **Preview Data**: Tampilan data sebelum proses lengkap
- **Export Data**: Ekspor hasil olahan ke file Excel baru
- **Progress Bar**: Indikator progres untuk file besar
- **Error Handling**: Penanganan error untuk file corrupt

## 📥 Instalasi

### 1. Install Python
Pastikan Python 3.8+ terinstall di komputer Anda:
- Download dari [python.org](https://python.org)

### 2. Install Dependencies
Buka Command Prompt atau PowerShell, lalu jalankan:
```bash
cd d:\12\test-excel-py
pip install -r requirements.txt
```

### 3. Generate Data Testing (Opsional)
Untuk membuat file contoh:
```bash
python generate_test_data.py
```

## 🎮 Cara Menggunakan

### 1. Menjalankan Aplikasi
```bash
python excel_importer.py
```

### 2. Memuat File Excel
- Klik tombol **Browse** untuk memilih file Excel
- Pilih file yang ingin diolah (.xlsx atau .xls)
- Klik **Load File** untuk memulai proses
- Progress bar akan menunjukkan status loading

### 3. Sorting Data
- **Klik header kolom** untuk mengurutkan data
- Klik sekali untuk ascending (A-Z, 0-9)
- Klik lagi untuk descending (Z-A, 9-0)
- Atau gunakan tombol **Sort Ascending**/**Sort Descending**

### 4. Filtering Data
- Pilih kolom dari dropdown **Filter by:**
- Masukkan nilai filter di kolom teks
- Klik **Apply Filter** untuk menerapkan filter
- Klik **Clear Filter** untuk menghapus filter

**Contoh Filter:**
- Teks: "jakarta" (cari yang mengandung teks)
- Angka: "5000000" (nilai tepat)
- Tanggal: "2023-01-15" (format tanggal)

### 5. Validasi Data
- Klik **Validate Data** untuk memeriksa kualitas data
- Aplikasi akan menampilkan:
  - Jumlah missing values per kolom
  - Deteksi tipe data tidak konsisten
  - Hasil pemeriksaan data

### 6. Export Data
- Klik **Export to Excel** untuk menyimpan data
- Pilih lokasi dan nama file
- Data yang diexport termasuk hasil filter/sorting

### 7. Melihat Statistik
- Klik **Show Statistics** untuk melihat ringkasan data
- Informasi yang ditampilkan:
  - Jumlah baris dan kolom
  - Tipe data setiap kolom
  - Statistik numerik (min, max, mean)
  - Missing values count

## ⚠️ Penanganan Error

### File Corrupt
- Jika file corrupt, aplikasi akan menampilkan pesan error
- Pastikan file Excel tidak sedang terbuka di program lain

### Format Tidak Sesuai
- Aplikasi mendukung .xlsx dan .xls
- Untuk file .xls, pastikan library xlrd terinstall

### Data Terlalu Besar
- Untuk file >100MB, pastikan RAM cukup
- Progress bar membantu memantau progres loading

### 🎯 Tips Penggunaan
- Gunakan pencarian global untuk menemukan data dengan cepat di semua kolom.
- Manfaatkan fitur **Reset Data** di dashboard web untuk membersihkan seluruh data riwayat export jika diperlukan.
- Tombol **Clear Sorting (X)** di dashboard web memudahkan pengembalian urutan data ke posisi semula tanpa harus me-reload halaman.

## 📝 Changelog

### v4.0.0 (2026-02-25)
- **Perbaikan Display Incremental**: Memperbaiki masalah nilai `INCREMENTAL 1` yang tidak muncul dengan mekanisme *intelligent column mapping* (merename `REVENUE INCREMENTAL 1` dan melakukan *merge data* jika kedua kolom ada).
- **Penghapusan Kolom Actual**: Menghapus secara permanen kolom `REVENUE (ACTUAL)` dari sistem (database ingestion dan tampilan dashboard) untuk standarisasi data.
- **Revamp Reset Data**: Memperbarui fungsi reset data dengan sistem transaksi SQLite (rollback jika gagal), pembersihan seluruh file residual (`merged_current.xlsx`), dan backup otomatis file excel sebelum dihapus.
- **Robust Error Handling**: Peningkatan logging pada level backend (`web_app.py`) dan pipeline (`process_export.py`) untuk pelacakan alur data yang lebih akurat.
- **Unit Testing v4**: Menambahkan integrasi test untuk memverifikasi pembersihan kolom dan konsistensi data setelah proses reset.

### v3.0.0 (2026-02-25)
- **Fitur Reset Data**: Menambahkan tombol "Reset Data" (ikon trash) di dashboard web untuk menghapus seluruh data permanen (SQLite & Excel) dengan konfirmasi keamanan.
- **Clear Sorting**: Menambahkan tombol "X" kecil di samping label sort pada dashboard web untuk menghapus pengurutan aktif.
- **Standarisasi Kolom**: 
  - Menghapus kolom "Revenue Incremental 1".
  - Menggantinya dengan kolom "Incremental 1" (tanpa prefix "Revenue").
  - Menyesuaikan urutan kolom tabel sesuai standar anggaran program (NOP, PROGRAM, ..., INCREMENTAL 1, 2, 3, STATUS, dsb).
- **Perbaikan Backend**: 
  - Update `process_export.py` untuk mendukung skema kolom baru.
  - Update `web_app.py` untuk merename dan mengurutkan kolom secara otomatis saat data dimuat.
- **Unit Testing**: Menambahkan `tests/test_dashboard_v3.py` untuk memverifikasi fungsi reset data dan penggantian nama kolom.
- **UI/UX**: Peningkatan responsivitas dashboard untuk perangkat mobile dan penambahan hover effects pada tombol-tombol baru.

### Performa Optimal
- Tutup aplikasi lain saat memproses file besar
- Gunakan filter untuk bekerja dengan subset data
- Export hasil sebelum memproses data sangat besar

### Format Data yang Disarankan
- Gunakan header pada baris pertama
- Hindari merged cells
- Pastikan tipe data konsisten dalam satu kolom

### Backup Data
- Selalu simpan backup file original
- Gunakan fitur export untuk menyimpan hasil olahan

## 🔧 Troubleshooting

### Error "No module named 'pandas'"
```bash
pip install pandas openpyxl
```

### Error Loading File
- Pastikan file tidak corrupt
- Coba buka file di Microsoft Excel terlebih dahulu

### Aplikasi Lambat
- Kurangi jumlah data yang ditampilkan
- Gunakan filtering untuk bekerja dengan data subset

## 📊 Spesifikasi Teknis

### Batasan
- Maksimum file size: ~100MB
- Maksimum rows: ~1,000,000 (tergantung RAM)
- Preview data: 1000 rows pertama

### Format yang Didukung
- ✅ .xlsx (Excel 2007+)
- ✅ .xls (Excel 97-2003)
- ❌ .csv (gunakan Save As Excel terlebih dahulu)

## 📞 Support

Untuk bantuan lebih lanjut:
1. Periksa file contoh yang digenerate
2. Pastikan semua dependencies terinstall
3. Coba dengan file kecil terlebih dahulu

## 🔄 Update Aplikasi

Untuk update versi terbaru:
```bash
pip install --upgrade pandas openpyxl
```

---

**Selamat Menggunakan Aplikasi Excel Importer!** 🎉

## 🧭 Langkah-Langkah Penggunaan (Ringkas)

1. Buka terminal/PowerShell dan pindah ke folder proyek:
   - `cd d:\12\test-excel-py`
2. Install dependencies (sekali saja):
   - `pip install -r requirements.txt`
3. Jalankan aplikasi desktop:
   - `python excel_importer.py`
4. Klik Browse → pilih file Excel → klik Load File.
5. Lakukan sorting dengan klik header kolom; filtering lewat panel “Filter by”.
6. Klik Validate Data untuk cek kualitas data (opsional).
7. Klik Export to Excel untuk menyimpan hasil filter/sort.
8. Setelah eksport:
   - Aplikasi otomatis menyiapkan file `dashboard_export.xlsx` untuk dashboard.
   - Browser akan terbuka ke web dashboard lokal (Flask).
9. Login ke dashboard:
   - Username: `admin`
   - Password: `admin123`  
   - (Bisa diubah melalui environment variable `DASHBOARD_USER` dan `DASHBOARD_PASSWORD`)
10. Di dashboard:
    - Gunakan pencarian global, sorting header tabel, dan pengaturan batas baris.
    - Pilih tipe grafik (Bar/Line/Pie) dan kolom kategori (X) serta nilai (Y).
    - Klik “Unduh sebagai PDF” untuk menyimpan tampilan grafik saat ini.
    - Klik “Reset tampilan” untuk mengembalikan semua kontrol ke pengaturan default.

## 🌐 Alur Export ke Web Dashboard

- Saat Anda klik “Export to Excel” di aplikasi desktop:
  - Hasil olahan disimpan ke lokasi yang Anda pilih.
  - Salinan untuk dashboard disimpan ke `d:\12\test-excel-py\dashboard_export.xlsx`.
  - Server Flask (`web_app.py`) diluncurkan otomatis dan membuka browser ke `http://127.0.0.1:5000/`.
- Dashboard membaca sheet `Data` dari `dashboard_export.xlsx` dan menampilkan tabel + grafik.
- Nilai kosong (NaN/NaT) otomatis dikonversi menjadi `null` agar data valid di JSON.

## 🔁 Reset Tampilan (Dashboard)

Tombol “Reset tampilan” mengembalikan:
- Pencarian global: kosong
- Data: kembali ke original (hapus filter aktif)
- Sorting: nonaktif (hapus indikator sort)
- Dropdown:  
  - Kolom prioritas → item pertama  
  - Batas baris → 50  
  - Tipe grafik → Bar  
  - Kolom X → item pertama  
  - Kolom Y → item kedua (jika tersedia)
- Scroll tabel: kembali ke posisi awal (top-left)
- Tabel dan grafik dirender ulang dengan pengaturan default

## 🧪 Testing Cepat

- Skenario 1: Sorting + Filter lalu Export  
  Pastikan data yang tampil di dashboard sesuai hasil filter/sort.
- Skenario 2: Ubah row limit, tipe grafik, kolom X/Y, lakukan sort, geser scroll, lalu klik “Reset tampilan”.  
  Semua elemen UI kembali ke default seperti daftar di atas.
- Jika dashboard menampilkan “0 baris”:
  - Pastikan `dashboard_export.xlsx` ada dan memiliki sheet `Data`
  - Hard refresh browser (Ctrl+F5)
  - Cek terminal Flask: tidak ada error JSON (NaN), dan log `[web_app] Loaded dataframe with shape: ...`

