@extends('layout')

@section('content')
<div class="flex flex-col gap-8">
    <!-- Chrome-style Tab Filter -->
    <div class="flex items-center gap-1 p-1 bg-slate-900/50 rounded-2xl border border-gray-800/50 w-fit mx-auto overflow-x-auto max-w-full no-scrollbar">
        <button onclick="switchTab('all')" id="tab-all" class="tab-btn active px-6 py-2 rounded-xl text-xs font-medium transition-all duration-200 flex items-center gap-2 whitespace-nowrap">
            <span>All Proposals</span>
            <span class="count-badge px-2 py-0.5 rounded-full bg-gray-800 text-[10px] text-gray-400">0</span>
        </button>
        <button onclick="switchTab('submitted')" id="tab-submitted" class="tab-btn px-6 py-2 rounded-xl text-xs font-medium transition-all duration-200 flex items-center gap-2 whitespace-nowrap">
            <span class="w-2 h-2 rounded-full bg-blue-500"></span>
            <span>Submitted</span>
            <span class="count-badge px-2 py-0.5 rounded-full bg-blue-900/30 text-[10px] text-blue-400">0</span>
        </button>
        <button onclick="switchTab('pending')" id="tab-pending" class="tab-btn px-6 py-2 rounded-xl text-xs font-medium transition-all duration-200 flex items-center gap-2 whitespace-nowrap">
            <span class="w-2 h-2 rounded-full bg-amber-500"></span>
            <span>Pending</span>
            <span class="count-badge px-2 py-0.5 rounded-full bg-amber-900/30 text-[10px] text-amber-400">0</span>
        </button>
        <button onclick="switchTab('approved')" id="tab-approved" class="tab-btn px-6 py-2 rounded-xl text-xs font-medium transition-all duration-200 flex items-center gap-2 whitespace-nowrap">
            <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>Approved</span>
            <span class="count-badge px-2 py-0.5 rounded-full bg-emerald-900/30 text-[10px] text-emerald-400">0</span>
        </button>
        <button onclick="switchTab('rejected')" id="tab-rejected" class="tab-btn px-6 py-2 rounded-xl text-xs font-medium transition-all duration-200 flex items-center gap-2 whitespace-nowrap">
            <span class="w-2 h-2 rounded-full bg-red-500"></span>
            <span>Rejected</span>
            <span class="count-badge px-2 py-0.5 rounded-full bg-red-900/30 text-[10px] text-red-400">0</span>
        </button>
    </div>

    <!-- Table Section (Top) -->
    <div class="glass p-6 rounded-3xl shadow-xl border border-gray-700/30 relative overflow-hidden">
        <!-- Table Loading Overlay -->
        <div id="tableLoader" class="absolute inset-0 z-20 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center opacity-0 pointer-events-none transition-opacity duration-300">
            <div class="flex flex-col items-center gap-3">
                <div class="w-10 h-10 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
                <span class="text-xs text-blue-400 font-medium tracking-wider">FILTERING DATA...</span>
            </div>
        </div>

        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
            <div>
                <h2 class="text-xl font-bold text-white tracking-wide">Tabel Data Dashboard</h2>
                <p class="text-xs text-gray-400">Sorting dan filtering interaktif untuk semua program.</p>
            </div>
            <div class="flex items-center gap-3">
                <span id="rowCountBadge" class="px-3 py-1 text-[10px] rounded-full bg-blue-900/30 border border-blue-500/30 text-blue-400 font-medium">0 baris</span>
            </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div class="space-y-1.5">
                <label class="text-[10px] text-gray-400 ml-1">Pencarian Global</label>
                <input type="text" id="globalSearch" placeholder="Cari di semua kolom..." 
                    class="w-full px-4 py-2 rounded-xl bg-slate-900/80 border border-slate-700/50 text-gray-200 text-xs focus:border-blue-500/50 outline-none transition-all">
            </div>
            <div class="space-y-1.5">
                <label class="text-[10px] text-gray-400 ml-1">Kolom Prioritas</label>
                <select id="primaryColumnSelect" class="w-full px-4 py-2 rounded-xl bg-slate-900/80 border border-slate-700/50 text-gray-200 text-xs outline-none cursor-pointer"></select>
            </div>
            <div class="space-y-1.5">
                <label class="text-[10px] text-gray-400 ml-1">Batas Baris</label>
                <select id="rowLimit" class="w-full px-4 py-2 rounded-xl bg-slate-900/80 border border-slate-700/50 text-gray-200 text-xs outline-none cursor-pointer">
                    <option value="50">50</option>
                    <option value="100">100</option>
                    <option value="250">250</option>
                    <option value="0">Semua</option>
                </select>
            </div>
        </div>

        <div class="rounded-2xl border border-gray-800/50 overflow-hidden bg-slate-900/30">
            <div class="max-h-[400px] overflow-auto scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent">
                <table id="dataTable" class="w-full text-[11px] text-left">
                    <thead class="sticky top-0 z-10 bg-slate-900 border-b border-gray-800"></thead>
                    <tbody class="divide-y divide-gray-800/30"></tbody>
                </table>
            </div>
        </div>

        <div class="mt-4 flex justify-between items-center text-[10px] text-gray-500">
            <div id="statusText">Memuat data...</div>
            <div id="sortStatusContainer" class="flex items-center gap-2">
                <span id="sortStatus"></span>
                <button id="clearSortBtn" class="hidden px-2 py-0.5 rounded bg-gray-800 hover:bg-gray-700 text-gray-300">X</button>
            </div>
        </div>
    </div>

    <!-- Chart Section (Bottom) -->
    <div class="glass p-6 rounded-3xl shadow-xl border border-gray-700/30">
        <div class="flex justify-between items-center mb-6">
            <div>
                <h2 class="text-xl font-bold text-white tracking-wide">Visualisasi Grafik</h2>
                <p class="text-xs text-gray-400">Pilih kolom dan tipe grafik untuk analisis.</p>
            </div>
            <div class="px-3 py-1 text-[10px] rounded-full bg-indigo-900/30 border border-indigo-500/30 text-indigo-400 font-medium">Interactive Chart</div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div class="space-y-1.5">
                <label class="text-[10px] text-gray-400 ml-1">Tipe Grafik</label>
                <select id="chartType" class="w-full px-4 py-2 rounded-xl bg-slate-900/80 border border-slate-700/50 text-gray-200 text-xs outline-none cursor-pointer">
                    <option value="bar">Bar</option>
                    <option value="line">Line</option>
                    <option value="pie">Pie</option>
                </select>
            </div>
            <div class="space-y-1.5">
                <label class="text-[10px] text-gray-400 ml-1">Kategori (X)</label>
                <select id="xColumn" class="w-full px-4 py-2 rounded-xl bg-slate-900/80 border border-slate-700/50 text-gray-200 text-xs outline-none cursor-pointer"></select>
            </div>
            <div class="space-y-1.5">
                <label class="text-[10px] text-gray-400 ml-1">Nilai (Y)</label>
                <select id="yColumn" class="w-full px-4 py-2 rounded-xl bg-slate-900/80 border border-slate-700/50 text-gray-200 text-xs outline-none cursor-pointer"></select>
            </div>
        </div>

        <div class="h-[400px] mb-6 rounded-2xl bg-slate-900/20 p-4 border border-gray-800/30">
            <canvas id="chartCanvas"></canvas>
        </div>

        <div class="flex gap-3 justify-end">
            <button id="downloadPdfBtn" class="px-4 py-2 rounded-full bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-900/20 transition-all">Unduh PDF</button>
            <button id="resetViewBtn" class="px-4 py-2 rounded-full bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-semibold transition-all">Reset View</button>
        </div>
    </div>
</div>

<style>
    .tab-btn { color: #94a3b8; border: 1px solid transparent; }
    .tab-btn:hover { background: rgba(30, 41, 59, 0.5); color: #e2e8f0; }
    .tab-btn.active { background: #1e293b; color: #3b82f6; border-color: rgba(59, 130, 246, 0.3); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); }
    .no-scrollbar::-webkit-scrollbar { display: none; }
    .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
@endsection

@push('scripts')
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script>
    let originalData = [];
    let filteredData = [];
    let columns = [];
    let currentSortColumn = null;
    let currentSortDirection = "asc";
    let chartInstance = null;
    let currentTab = 'all';

    function fetchData() {
        const statusText = document.getElementById("statusText");
        statusText.textContent = "Memuat data dari server...";
        fetch("{{ url('/api/data') }}")
            .then(res => res.json())
            .then(data => {
                columns = data.columns || [];
                originalData = data.rows || [];
                
                updateTabCounts();
                applyFilter(); // Initial filter apply
                
                buildTable();
                initControls();
                statusText.textContent = `Berhasil memuat ${originalData.length} baris.`;
            })
            .catch(err => {
                console.error(err);
                statusText.textContent = "Gagal memuat data.";
            });
    }

    function updateTabCounts() {
        const counts = {
            all: originalData.length,
            submitted: originalData.filter(r => r.STATUS === 'SUBMITTED').length,
            approved: originalData.filter(r => r.STATUS === 'APPROVED').length,
            pending: originalData.filter(r => r.STATUS === 'PENDING').length,
            rejected: originalData.filter(r => r.STATUS === 'REJECTED').length
        };

        Object.keys(counts).forEach(key => {
            const badge = document.querySelector(`#tab-${key} .count-badge`);
            if (badge) badge.textContent = counts[key];
        });
    }

    function switchTab(tab) {
        if (currentTab === tab) return;
        
        // Show loader
        const loader = document.getElementById("tableLoader");
        loader.classList.add('opacity-100');
        
        // Update UI
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.getElementById(`tab-${tab}`).classList.add('active');
        
        currentTab = tab;
        
        // Small delay to show loading state
        setTimeout(() => {
            applyFilter();
            loader.classList.remove('opacity-100');
        }, 300);
    }

    function buildTable() {
        const thead = document.querySelector("#dataTable thead");
        thead.innerHTML = "";
        const headerRow = document.createElement("tr");
        columns.forEach(col => {
            const th = document.createElement("th");
            th.className = "px-4 py-3 font-semibold text-gray-400 cursor-pointer hover:bg-gray-800/50 transition-colors whitespace-nowrap";
            th.textContent = col;
            th.addEventListener("click", () => onHeaderClick(col, th));
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        renderRows();
    }

    function renderRows() {
        const tbody = document.querySelector("#dataTable tbody");
        tbody.innerHTML = "";
        const limitValue = parseInt(document.getElementById("rowLimit").value);
        const rows = limitValue > 0 ? filteredData.slice(0, limitValue) : filteredData;
        
        if (rows.length === 0) {
            tbody.innerHTML = `<tr><td colspan="${columns.length}" class="px-6 py-12 text-center text-gray-500 italic">Tidak ada data ditemukan untuk kategori ini.</td></tr>`;
        } else {
            rows.forEach(row => {
                const tr = document.createElement("tr");
                tr.className = "hover:bg-blue-500/5 transition-colors group";
                columns.forEach(col => {
                    const td = document.createElement("td");
                    td.className = "px-4 py-2.5 border-b border-gray-800/30 group-last:border-0 whitespace-nowrap";
                    const val = row[col];
                    td.textContent = (val === null || val === undefined) ? "" : val;
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
        }
        
        document.getElementById("rowCountBadge").textContent = `${filteredData.length} baris`;
    }

    function onHeaderClick(column, th) {
        if (currentSortColumn === column) {
            currentSortDirection = currentSortDirection === "asc" ? "desc" : "asc";
        } else {
            currentSortColumn = column;
            currentSortDirection = "asc";
        }
        
        filteredData.sort((a, b) => {
            let va = a[column], vb = b[column];
            if (va === vb) return 0;
            if (va === null) return 1;
            if (vb === null) return -1;
            
            if (!isNaN(parseFloat(va)) && !isNaN(parseFloat(vb))) {
                return currentSortDirection === "asc" ? va - vb : vb - va;
            }
            
            va = String(va).toLowerCase();
            vb = String(vb).toLowerCase();
            return currentSortDirection === "asc" ? (va < vb ? -1 : 1) : (va < vb ? 1 : -1);
        });
        
        document.querySelectorAll("#dataTable th").forEach(t => t.classList.remove("text-blue-400"));
        th.classList.add("text-blue-400");
        document.getElementById("sortStatus").textContent = `Sort: ${column} (${currentSortDirection})`;
        document.getElementById("clearSortBtn").classList.remove("hidden");
        renderRows();
        renderChart();
    }

    function initControls() {
        const xSelect = document.getElementById("xColumn");
        const ySelect = document.getElementById("yColumn");
        const primarySelect = document.getElementById("primaryColumnSelect");
        
        [xSelect, ySelect, primarySelect].forEach(s => s.innerHTML = "");
        
        columns.forEach((col, idx) => {
            const opt = document.createElement("option");
            opt.value = col; opt.textContent = col;
            xSelect.appendChild(opt.cloneNode(true));
            ySelect.appendChild(opt.cloneNode(true));
            primarySelect.appendChild(opt.cloneNode(true));
        });
        
        if (columns.length > 1) ySelect.selectedIndex = 1;

        document.getElementById("globalSearch").addEventListener("input", applyFilter);
        document.getElementById("rowLimit").addEventListener("change", renderRows);
        document.getElementById("chartType").addEventListener("change", renderChart);
        xSelect.addEventListener("change", renderChart);
        ySelect.addEventListener("change", renderChart);
        document.getElementById("resetViewBtn").addEventListener("click", () => {
            document.getElementById("globalSearch").value = "";
            switchTab('all');
        });
        document.getElementById("clearSortBtn").addEventListener("click", () => {
            currentSortColumn = null;
            document.getElementById("clearSortBtn").classList.add("hidden");
            document.getElementById("sortStatus").textContent = "";
            applyFilter();
        });
        
        renderChart();
    }

    function applyFilter() {
        const term = document.getElementById("globalSearch").value.toLowerCase();
        
        // 1. Filter by Tab
        let tempFiltered = originalData;
        if (currentTab !== 'all') {
            tempFiltered = originalData.filter(r => r.STATUS === currentTab.toUpperCase());
        }
        
        // 2. Filter by Global Search
        filteredData = tempFiltered.filter(row => 
            columns.some(col => String(row[col]).toLowerCase().includes(term))
        );
        
        renderRows();
        renderChart();
    }

    function renderChart() {
        const xCol = document.getElementById("xColumn").value;
        const yCol = document.getElementById("yColumn").value;
        const type = document.getElementById("chartType").value;
        
        if (!xCol || !yCol) return;
        
        const grouped = {};
        filteredData.forEach(row => {
            const key = row[xCol];
            const val = parseFloat(row[yCol]) || 0;
            grouped[key] = (grouped[key] || 0) + val;
        });
        
        const labels = Object.keys(grouped);
        const data = Object.values(grouped);
        
        if (chartInstance) chartInstance.destroy();
        
        chartInstance = new Chart(document.getElementById("chartCanvas"), {
            type: type,
            data: {
                labels: labels,
                datasets: [{
                    label: `${yCol} per ${xCol}`,
                    data: data,
                    backgroundColor: type === 'pie' ? labels.map((_, i) => `hsl(${i * 360 / labels.length}, 70%, 50%)`) : '#3b82f6',
                    borderColor: '#1e293b',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#94a3b8', font: { size: 10 } } }
                },
                scales: type === 'pie' ? {} : {
                    y: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8', font: { size: 9 } } },
                    x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 9 }, maxRotation: 45, minRotation: 45 } }
                }
            }
        });
    }

    document.addEventListener("DOMContentLoaded", fetchData);
</script>
@endpush

