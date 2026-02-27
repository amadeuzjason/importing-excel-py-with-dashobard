<?php
try {
    $db = new SQLite3('data_pipeline.sqlite');
    $res = $db->query('SELECT COUNT(*) FROM records_current');
    if ($res) {
        echo "Data found: " . $res->fetchArray()[0] . "\n";
    } else {
        echo "Query failed.\n";
    }
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
