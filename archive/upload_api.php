<?php

require __DIR__ . '/vendor/autoload.php';

use Rutube\Rutube;

// Configuration
$login = 'nlpkem@ya.ru';
$password = '*V8u2p2r';
$videoPath = __DIR__ . '/test_video.mp4'; // Path to video in current dir
$title = 'Test Video API PHP';
$description = 'Uploaded via PHP API Client';
$categoryId = 13; // Hobbies? Or default.
$isHidden = 0; // Public

echo "--- Rutube PHP API Uploader ---
";

if (!file_exists($videoPath)) {
    die("Error: Video file not found at $videoPath\n");
}

try {
    echo "1. Initializing client and authorizing...\n";
    // The constructor calls authorize() internally
    $rutube = new Rutube($login, $password);

    if ($rutube->isAuthorized()) {
        echo "✅ Authorized successfully!\n";
    } else {
        echo "❌ Authorization failed (no token returned).\n";
        exit;
    }

    echo "2. Fetching account info...\n";
    $account = $rutube->account()->info();
    print_r($account);

} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
    // Print stack trace for debugging
    echo $e->getTraceAsString() . "\n";
}

