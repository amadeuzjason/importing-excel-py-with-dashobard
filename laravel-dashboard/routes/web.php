<?php

use App\Http\Controllers\AuthController;
use App\Http\Controllers\DashboardController;
use Illuminate\Support\Facades\Route;

Route::get('/login', [AuthController::class, 'showLogin'])->name('login');
Route::post('/login', [AuthController::class, 'login']);
Route::post('/logout', [AuthController::class, 'logout'])->name('logout');

Route::middleware(['custom_auth'])->group(function () {
    Route::get('/', [DashboardController::class, 'index'])->name('dashboard');
    Route::get('/approvals', [DashboardController::class, 'approvals'])->name('approvals');
    Route::post('/api/approve', [DashboardController::class, 'approve']);
    Route::post('/api/reject', [DashboardController::class, 'reject']);
    Route::get('/api/data', [DashboardController::class, 'apiData']);
});
