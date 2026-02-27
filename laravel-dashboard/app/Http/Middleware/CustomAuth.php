<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Session;

class CustomAuth
{
    public function handle(Request $request, Closure $next)
    {
        if (!Session::has('logged_in')) {
            return redirect()->route('login');
        }

        return $next($request);
    }
}
