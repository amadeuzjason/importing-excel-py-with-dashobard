<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Session;

class AuthController extends Controller
{
    private $users = [
        'NOP-PALU' => 'palu123',
        'NOP-MKS' => 'mks123',
        'NOP-MANADO' => 'manado123',
        'admin' => 'admin123'
    ];

    public function showLogin()
    {
        if (Session::has('logged_in')) {
            return redirect()->route('dashboard');
        }
        return view('login');
    }

    public function login(Request $request)
    {
        $username = $request->input('username');
        $password = $request->input('password');

        if (isset($this->users[$username]) && $this->users[$username] === $password) {
            Session::put('logged_in', true);
            Session::put('username', $username);
            return redirect()->route('dashboard');
        }

        return back()->with('error', 'Username atau password salah.');
    }

    public function logout()
    {
        Session::forget(['logged_in', 'username']);
        return redirect()->route('login');
    }
}
