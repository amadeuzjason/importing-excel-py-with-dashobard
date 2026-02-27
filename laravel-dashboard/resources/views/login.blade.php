@extends('layout')

@section('content')
<div class="flex items-center justify-center min-h-[70vh]">
    <div class="glass max-w-sm w-full p-8 rounded-3xl shadow-2xl shadow-black/50 border border-gray-700/50 backdrop-blur-2xl">
        <div class="mb-6 text-center">
            <h1 class="text-2xl font-bold text-white mb-2">Masuk ke Dashboard</h1>
            <p class="text-sm text-gray-400">Gunakan akun regional Anda untuk mengakses visualisasi data.</p>
        </div>

        @if(session('error'))
        <div class="mb-4 p-3 rounded-lg bg-red-900/30 border border-red-500/50 text-red-400 text-xs">
            {{ session('error') }}
        </div>
        @endif

        <form action="{{ route('login') }}" method="POST" class="space-y-5">
            @csrf
            <div>
                <label for="username" class="block text-xs text-gray-400 mb-1.5 ml-1">Username</label>
                <input type="text" name="username" id="username" required 
                    class="w-full px-4 py-2.5 rounded-xl bg-slate-900/80 border border-slate-700/50 text-gray-200 text-sm focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 outline-none transition-all">
            </div>
            <div>
                <label for="password" class="block text-xs text-gray-400 mb-1.5 ml-1">Password</label>
                <input type="password" name="password" id="password" required 
                    class="w-full px-4 py-2.5 rounded-xl bg-slate-900/80 border border-slate-700/50 text-gray-200 text-sm focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 outline-none transition-all">
            </div>
            <button type="submit" 
                class="w-full py-3 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-blue-900/20 transition-all hover:-translate-y-0.5 active:translate-y-0">
                Masuk
            </button>
        </form>

        <div class="mt-8 pt-6 border-t border-gray-800/50 text-[10px] text-gray-600 space-y-1">
            <p>Akun yang tersedia:</p>
            <ul class="list-disc list-inside">
                <li>NOP-PALU / palu123</li>
                <li>NOP-MKS / mks123</li>
                <li>NOP-MANADO / manado123</li>
            </ul>
        </div>
    </div>
</div>
@endsection
