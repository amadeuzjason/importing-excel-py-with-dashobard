<?php

namespace App\Http\Controllers;

use App\Services\SQLiteService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Session;

class DashboardController extends Controller
{
    protected $sqlite;

    public function __construct(SQLiteService $sqlite)
    {
        $this->sqlite = $sqlite;
    }

    public function index()
    {
        $df = $this->loadData();
        return view('dashboard', [
            'columns' => $df['columns'],
            'rows' => $df['rows'],
            'username' => Session::get('username')
        ]);
    }

    public function approvals()
    {
        $df = $this->loadData();
        return view('approvals', [
            'rows' => $df['rows'],
            'username' => Session::get('username')
        ]);
    }

    public function approve(Request $request)
    {
        $nop = $request->input('nop');
        $username = Session::get('username');

        // Check if NOP exists
        $rows = $this->sqlite->query('SELECT * FROM records_current WHERE "NOP" = :nop', [':nop' => $nop]);
        if (empty($rows)) {
            return response()->json(['error' => 'NOP tidak ditemukan.'], 404);
        }

        // Update approval
        $this->sqlite->execute('UPDATE records_current SET "STATUS" = :status, "APPROVED BY" = :approved_by WHERE "NOP" = :nop', [
            ':status' => 'APPROVED',
            ':approved_by' => $username,
            ':nop' => $nop
        ]);

        return response()->json(['message' => "Proposal $nop telah disetujui oleh $username."]);
    }

    public function reject(Request $request)
    {
        $nop = $request->input('nop');
        $username = Session::get('username');

        // Update rejection
        $this->sqlite->execute('UPDATE records_current SET "STATUS" = :status, "APPROVED BY" = :approved_by WHERE "NOP" = :nop', [
            ':status' => 'REJECTED',
            ':approved_by' => $username,
            ':nop' => $nop
        ]);

        return response()->json(['message' => "Proposal $nop telah ditolak oleh $username."]);
    }

    public function apiData()
    {
        $df = $this->loadData();
        return response()->json($df);
    }

    private function loadData()
    {
        try {
            $allCols = $this->sqlite->getColumns('records_current');
            
            // 1. Define base columns to keep (standard 17 columns minus internal/actual)
            $desiredOrder = [
                "NOP", "PROGRAM", "KATEGORI", "JUSTIFIKASI", "PROPOSAL", "BUDGET", 
                "REVENUE", "COST", "PROFIT", "INCREMENTAL 1", "INCREMENTAL 2", 
                "INCREMENTAL 3", "STATUS", "PILOT", "DRIVEN PROGRAM", "ASSIGN BY", 
                "APPROVED BY"
            ];

            // 2. Fetch data
            $rows = $this->sqlite->query("SELECT * FROM records_current");
            
            // 3. Process each row for column normalization
            $processedRows = array_map(function($row) {
                // Rename REVENUE INCREMENTAL 1 to INCREMENTAL 1 if it exists and INCREMENTAL 1 is empty
                if (isset($row['REVENUE INCREMENTAL 1'])) {
                    if (!isset($row['INCREMENTAL 1']) || empty($row['INCREMENTAL 1'])) {
                        $row['INCREMENTAL 1'] = $row['REVENUE INCREMENTAL 1'];
                    }
                }
                
                // Remove unwanted columns
                unset($row['REVENUE (ACTUAL)']);
                unset($row['REVENUE INCREMENTAL 1']);
                unset($row['row_hash']);
                unset($row['ingest_timestamp']);
                unset($row['source_file']);
                unset($row['ExportSource']);
                unset($row['ExportTimestamp']);
                unset($row['ExportUser']);
                
                return $row;
            }, $rows);

            // 4. Determine final visible columns based on desired order
            $finalCols = array_values(array_intersect($desiredOrder, array_keys($processedRows[0] ?? [])));

            return [
                'columns' => $finalCols,
                'rows' => $processedRows
            ];
        } catch (\Exception $e) {
            return [
                'columns' => [],
                'rows' => [],
                'error' => $e->getMessage()
            ];
        }
    }
}
