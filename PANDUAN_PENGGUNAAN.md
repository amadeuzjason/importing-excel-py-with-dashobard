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

## 🎯 Tips Penggunaan

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