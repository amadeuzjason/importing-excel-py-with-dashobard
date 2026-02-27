<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Excel Data Studio - Laravel</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background: radial-gradient(circle at top, #1f2937 0, #020617 55%, #000 100%); color: #e5e7eb; min-height: 100vh; }
        .glass { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(12px); border: 1px solid rgba(148, 163, 184, 0.2); }
    </style>
</head>
<body>
    <div class="min-h-screen flex flex-col">
        @if(Session::has('logged_in'))
        <nav class="glass sticky top-0 z-50 border-b border-blue-900/50">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16 items-center">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-indigo-600 shadow-lg shadow-blue-500/20"></div>
                        <div>
                            <div class="text-sm font-bold tracking-wider uppercase">Excel Data Studio</div>
                            <div class="text-[10px] text-gray-400">Interactive Analytics Workspace</div>
                        </div>
                    </div>
                    <div class="hidden md:flex items-center gap-6">
                        <a href="{{ route('dashboard') }}" class="text-sm {{ Request::is('/') ? 'text-blue-400 font-semibold' : 'text-gray-400 hover:text-white' }} transition-colors">Dashboard</a>
                        <a href="{{ route('approvals') }}" class="text-sm {{ Request::is('approvals') ? 'text-blue-400 font-semibold' : 'text-gray-400 hover:text-white' }} transition-colors">Approvals</a>
                        <div class="h-4 w-px bg-gray-700"></div>
                        <span class="text-xs text-gray-400">{{ Session::get('username') }}</span>
                        <form action="{{ route('logout') }}" method="POST" class="inline">
                            @csrf
                            <button type="submit" class="text-xs text-red-400 hover:text-red-300 transition-colors">Logout</button>
                        </form>
                    </div>
                </div>
            </div>
        </nav>
        @endif

        <main class="flex-grow p-4 md:p-8">
            <div class="max-w-7xl mx-auto">
                @yield('content')
            </div>
        </main>

        <footer class="p-6 text-center text-xs text-gray-500 border-t border-gray-800/50">
            Excel Data Studio · Laravel Edition · Local Analytics Workspace
        </footer>
    </div>
    @stack('scripts')
</body>
</html>
