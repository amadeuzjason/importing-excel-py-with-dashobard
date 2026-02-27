<?php

namespace App\Services;

use SQLite3;
use Exception;

class SQLiteService
{
    protected $db;

    public function __construct()
    {
        $dbPath = config('database.sqlite_path');
        if (!file_exists($dbPath)) {
            // Try fallback
            $dbPath = base_path('database/database.sqlite');
        }
        $this->db = new SQLite3($dbPath);
    }

    public function query($sql, $params = [])
    {
        $stmt = $this->db->prepare($sql);
        if (!$stmt) {
            throw new Exception($this->db->lastErrorMsg());
        }

        foreach ($params as $key => $value) {
            $stmt->bindValue($key, $value);
        }

        $result = $stmt->execute();
        if (!$result) {
            throw new Exception($this->db->lastErrorMsg());
        }

        $rows = [];
        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $rows[] = $row;
        }

        return $rows;
    }

    public function execute($sql, $params = [])
    {
        $stmt = $this->db->prepare($sql);
        if (!$stmt) {
            throw new Exception($this->db->lastErrorMsg());
        }

        foreach ($params as $key => $value) {
            $stmt->bindValue($key, $value);
        }

        return $stmt->execute();
    }

    public function getColumns($table)
    {
        $res = $this->db->query("PRAGMA table_info(\"$table\")");
        $cols = [];
        while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
            $cols[] = $row['name'];
        }
        return $cols;
    }
}
