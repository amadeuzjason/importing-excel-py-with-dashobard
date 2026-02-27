@extends('layout')

@section('content')
<div class="glass p-8 rounded-3xl shadow-2xl border border-gray-700/30">
    <div class="flex justify-between items-center mb-8">
        <div>
            <h2 class="text-2xl font-bold text-white tracking-tight">Assignment & Approvals</h2>
            <p class="text-sm text-gray-400">Kelola persetujuan proposal program regional.</p>
        </div>
        <div class="flex items-center gap-4">
            <div id="pendingCount" class="px-4 py-1.5 rounded-full bg-amber-900/20 border border-amber-500/30 text-amber-400 text-xs font-semibold">0 Pending</div>
        </div>
    </div>

    <div class="mb-6">
        <div class="relative max-w-md">
            <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            </span>
            <input type="text" id="approvalSearch" placeholder="Cari NOP atau Program..." 
                class="block w-full pl-10 pr-4 py-2.5 rounded-2xl bg-slate-900/80 border border-slate-700/50 text-gray-200 text-sm focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 outline-none transition-all">
        </div>
    </div>

    <div class="rounded-2xl border border-gray-800/50 overflow-hidden bg-slate-900/30">
        <div class="max-h-[600px] overflow-auto scrollbar-thin">
            <table id="approvalTable" class="w-full text-sm text-left">
                <thead class="sticky top-0 z-10 bg-slate-900 border-b border-gray-800">
                    <tr>
                        <th class="px-6 py-4 font-semibold text-gray-400">NOP</th>
                        <th class="px-6 py-4 font-semibold text-gray-400">PROGRAM</th>
                        <th class="px-6 py-4 font-semibold text-gray-400">BUDGET</th>
                        <th class="px-6 py-4 font-semibold text-gray-400">ASSIGN BY</th>
                        <th class="px-6 py-4 font-semibold text-gray-400">APPROVED BY</th>
                        <th class="px-6 py-4 font-semibold text-gray-400">STATUS</th>
                        <th class="px-6 py-4 font-semibold text-gray-400 text-right">AKSI</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-800/30" id="approvalBody">
                    <!-- Data will be loaded via JS -->
                </tbody>
            </table>
        </div>
    </div>
</div>

<div id="toast" class="fixed bottom-8 right-8 px-6 py-3 rounded-2xl glass border border-blue-500/30 text-white text-sm opacity-0 pointer-events-none transition-all duration-300 transform translate-y-4"></div>
@endsection

@push('scripts')
<script>
    let rows = [];

    async function fetchApprovals() {
        const resp = await fetch("{{ url('/api/data') }}");
        const data = await resp.json();
        rows = data.rows || [];
        renderApprovals();
    }

    function renderApprovals() {
        const body = document.getElementById("approvalBody");
        const term = document.getElementById("approvalSearch").value.toLowerCase();
        body.innerHTML = "";
        
        let pending = 0;
        const filtered = rows.filter(r => 
            String(r.NOP).toLowerCase().includes(term) || 
            String(r.PROGRAM).toLowerCase().includes(term)
        );

        filtered.forEach(row => {
            if (row.STATUS !== 'APPROVED' && row.STATUS !== 'REJECTED') pending++;
            
            const tr = document.createElement("tr");
            tr.className = "hover:bg-blue-500/5 transition-colors group";
            
            const statusClass = row.STATUS === 'APPROVED' ? 'text-green-400 bg-green-400/10' : 
                              (row.STATUS === 'REJECTED' ? 'text-red-400 bg-red-400/10' : 'text-amber-400 bg-amber-400/10');

            tr.innerHTML = `
                <td class="px-6 py-4 font-medium text-white">${row.NOP}</td>
                <td class="px-6 py-4 text-gray-400">${row.PROGRAM}</td>
                <td class="px-6 py-4 text-gray-400">${row.BUDGET || 0}</td>
                <td class="px-6 py-4 text-gray-400">${row['ASSIGN BY'] || '-'}</td>
                <td class="px-6 py-4 text-gray-400">${row['APPROVED BY'] || '-'}</td>
                <td class="px-6 py-4">
                    <span class="px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase ${statusClass}">${row.STATUS || 'PENDING'}</span>
                </td>
                <td class="px-6 py-4 text-right">
                    ${(row.STATUS !== 'APPROVED' && row.STATUS !== 'REJECTED') ? `
                        <div class="flex justify-end gap-2">
                            <button onclick="handleAction('${row.NOP}', 'approve')" class="px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-500 text-white text-xs font-semibold transition-all">Approve</button>
                            <button onclick="handleAction('${row.NOP}', 'reject')" class="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-semibold transition-all">Reject</button>
                        </div>
                    ` : '<span class="text-[10px] text-gray-600 italic">No Action</span>'}
                </td>
            `;
            body.appendChild(tr);
        });
        
        document.getElementById("pendingCount").textContent = `${pending} Pending`;
    }

    async function handleAction(nop, action) {
        const url = action === 'approve' ? "{{ url('/api/approve') }}" : "{{ url('/api/reject') }}";
        try {
            const resp = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': '{{ csrf_token() }}'
                },
                body: JSON.stringify({ nop })
            });
            const result = await resp.json();
            if (resp.ok) {
                showToast(result.message);
                fetchApprovals();
            } else {
                showToast(result.error, true);
            }
        } catch (err) {
            showToast("Terjadi kesalahan sistem.", true);
        }
    }

    function showToast(msg, isError = false) {
        const toast = document.getElementById("toast");
        toast.textContent = msg;
        toast.className = `fixed bottom-8 right-8 px-6 py-3 rounded-2xl glass border ${isError ? 'border-red-500/50 bg-red-900/20' : 'border-blue-500/50 bg-blue-900/20'} text-white text-sm opacity-100 pointer-events-auto transform translate-y-0`;
        setTimeout(() => {
            toast.className = toast.className.replace('opacity-100', 'opacity-0').replace('translate-y-0', 'translate-y-4');
        }, 3000);
    }

    document.getElementById("approvalSearch").addEventListener("input", renderApprovals);
    document.addEventListener("DOMContentLoaded", fetchApprovals);
</script>
@endpush
