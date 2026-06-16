<?php
ini_set('display_errors', '1');
ini_set('display_startup_errors', '1');
error_reporting(E_ALL);
header('Content-Type: application/json; charset=utf-8');
set_time_limit(0);

$ROOT = realpath(__DIR__ . '/../../../..');
$documentRoot = isset($_SERVER['DOCUMENT_ROOT']) ? realpath($_SERVER['DOCUMENT_ROOT']) : false;
$openBasedir = ini_get('open_basedir');
@file_put_contents('/tmp/api_debug.log', json_encode([
    'script_dir' => __DIR__,
    'root' => $ROOT,
    'document_root' => $documentRoot,
    'open_basedir' => $openBasedir,
], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\n", FILE_APPEND);
if ($ROOT === false) {
    http_response_code(500);
    echo json_encode(['error' => 'No se pudo resolver el directorio raíz.']);
    exit;
}

function json_error($message, $code = 400, $debug = [])
{
    $payload = ['error' => $message];
    if (isset($_GET['debug']) && $_GET['debug']) {
        $payload['_debug'] = array_merge([
            'script_dir' => __DIR__,
            'root' => $GLOBALS['ROOT'],
            'document_root' => isset($_SERVER['DOCUMENT_ROOT']) ? $_SERVER['DOCUMENT_ROOT'] : null,
            'open_basedir' => ini_get('open_basedir'),
            'raw_get' => $_GET,
            'raw_post' => $_POST,
        ], $debug);
    }
    http_response_code($code);
    echo json_encode($payload);
    exit;
}

function debug_info()
{
    $info = [
        'script_dir' => __DIR__,
        'root' => $GLOBALS['ROOT'],
        'document_root' => isset($_SERVER['DOCUMENT_ROOT']) ? $_SERVER['DOCUMENT_ROOT'] : null,
        'open_basedir' => ini_get('open_basedir'),
    ];
    return $info;
}

function normalize_path($raw)
{
    global $ROOT;
    if ($raw === '' || $raw === '.' || $raw === './') {
        return $ROOT;
    }
    $raw = str_replace('\\', '/', $raw);
    $raw = preg_replace('#/+#', '/', $raw);

    if (strpos($raw, '/') === 0) {
        $candidate = $raw;
    } else {
        $candidate = rtrim($ROOT, '/') . '/' . ltrim($raw, '/');
    }

    $parts = array_filter(explode('/', $candidate), function ($part) {
        return $part !== '';
    });
    $resolved = [];
    foreach ($parts as $part) {
        if ($part === '.') {
            continue;
        }
        if ($part === '..') {
            array_pop($resolved);
            continue;
        }
        $resolved[] = $part;
    }

    $resolvedPath = '/' . implode('/', $resolved);
    if (!is_dir($resolvedPath)) {
        return '';
    }
    if (strpos($resolvedPath, $ROOT) !== 0) {
        return '';
    }
    return $resolvedPath;
}

function is_allowed_path($path)
{
    global $ROOT;
    return $path !== '' && strpos($path, $ROOT) === 0;
}

function list_directory_entries($path)
{
    $entries = [];
    $items = @scandir($path);
    if ($items === false) {
        $dir = @opendir($path);
        if ($dir === false) {
            return $entries;
        }
        while (($name = readdir($dir)) !== false) {
            if ($name === '.' || $name === '..') {
                continue;
            }
            $full = $path . DIRECTORY_SEPARATOR . $name;
            $entries[] = [
                'name' => $name,
                'path' => $full,
                'is_dir' => is_dir($full),
                'is_file' => is_file($full),
            ];
        }
        closedir($dir);
    } else {
        foreach ($items as $name) {
            if ($name === '.' || $name === '..') {
                continue;
            }
            $full = $path . DIRECTORY_SEPARATOR . $name;
            $entries[] = [
                'name' => $name,
                'path' => $full,
                'is_dir' => is_dir($full),
                'is_file' => is_file($full),
            ];
        }
    }
    usort($entries, function ($a, $b) {
        if ($a['is_dir'] === $b['is_dir']) {
            return strcasecmp($a['name'], $b['name']);
        }
        return $a['is_dir'] ? -1 : 1;
    });
    return $entries;
}

function get_progress_path($folder)
{
    $hash = hash('sha256', $folder);
    return sys_get_temp_dir() . DIRECTORY_SEPARATOR . "audio_analysis_progress_{$hash}.log";
}

function update_progress($progressFile, $line)
{
    $line = trim($line);
    if ($line === '') {
        return;
    }
    $existing = [];
    if (is_file($progressFile)) {
        $existing = explode("\n", trim(file_get_contents($progressFile)));
    }
    $existing[] = $line;
    $existing = array_slice($existing, -100);
    file_put_contents($progressFile, implode("\n", $existing) . "\n");
}

function get_progress_lines($progressFile)
{
    if (!is_file($progressFile)) {
        return [];
    }
    $content = trim(@file_get_contents($progressFile));
    return $content === '' ? [] : explode("\n", $content);
}

function list_results($folder)
{
    $parent = dirname($folder);
    $resultsDir = $parent . DIRECTORY_SEPARATOR . 'resultados';
    $files = [];
    if (!is_dir($resultsDir)) {
        return $files;
    }
    $items = @scandir($resultsDir);
    if ($items === false) {
        return $files;
    }
    foreach ($items as $name) {
        if ($name === '.' || $name === '..') {
            continue;
        }
        $full = $resultsDir . DIRECTORY_SEPARATOR . $name;
        if (is_file($full)) {
            $files[] = ['name' => $name, 'path' => $full];
        }
    }
    usort($files, function ($a, $b) {
        return strcasecmp($a['name'], $b['name']);
    });
    return $files;
}

$action = $_GET['action'] ?? $_POST['action'] ?? null;
if (!$action) {
    json_error('Falta el parámetro action.', 400);
}

if ($action === 'list') {
    $rawPath = $_GET['path'] ?? '';
    $folder = normalize_path($rawPath);
    $isAllowed = $folder ? is_allowed_path($folder) : false;
    $isDir = $folder ? is_dir($folder) : false;
    if (!$folder || !$isAllowed || !$isDir) {
        $debug = isset($_GET['debug']) && $_GET['debug'] ? [
            'rawPath' => $rawPath,
            'normalized' => $folder,
            'is_allowed' => $isAllowed,
            'is_dir' => $isDir,
            'root' => $ROOT,
            'document_root' => isset($_SERVER['DOCUMENT_ROOT']) ? $_SERVER['DOCUMENT_ROOT'] : null,
            'open_basedir' => ini_get('open_basedir'),
        ] : [];
        json_error('Ruta no válida o carpeta no accesible.', 400, $debug);
    }
    $payload = ['folder' => $folder, 'entries' => list_directory_entries($folder)];
    if (isset($_GET['debug']) && $_GET['debug']) {
        $payload['_debug'] = [
            'rawPath' => $rawPath,
            'normalized' => $folder,
            'is_allowed' => $isAllowed,
            'is_dir' => $isDir,
            'root' => $ROOT,
            'document_root' => isset($_SERVER['DOCUMENT_ROOT']) ? $_SERVER['DOCUMENT_ROOT'] : null,
            'open_basedir' => ini_get('open_basedir'),
        ];
    }
    echo json_encode($payload);
    exit;
}

if ($action === 'results') {
    $rawFolder = $_GET['folder'] ?? '';
    $folder = normalize_path($rawFolder);
    if (!$folder || !is_allowed_path($folder) || !is_dir($folder)) {
        json_error('Ruta no válida o carpeta no accesible.', 400);
    }
    echo json_encode(['results' => list_results($folder)]);
    exit;
}

if ($action === 'status') {
    $rawFolder = $_GET['folder'] ?? '';
    $folder = normalize_path($rawFolder);
    if (!$folder || !is_allowed_path($folder) || !is_dir($folder)) {
        json_error('Ruta no válida o carpeta no accesible.', 400);
    }
    $progressFile = get_progress_path($folder);
    echo json_encode(['lines' => get_progress_lines($progressFile)]);
    exit;
}

if ($action === 'download') {
    $rawFolder = $_GET['folder'] ?? '';
    $fileName = $_GET['file'] ?? '';
    $folder = normalize_path($rawFolder);
    if (!$folder || !is_allowed_path($folder) || !is_dir($folder)) {
        json_error('Ruta no válida o carpeta no accesible.', 400);
    }
    $resultsDir = dirname($folder) . DIRECTORY_SEPARATOR . 'resultados';
    $safeFile = basename($fileName);
    $filePath = realpath($resultsDir . DIRECTORY_SEPARATOR . $safeFile);
    if (!$filePath || strpos($filePath, $resultsDir) !== 0 || !is_file($filePath)) {
        json_error('Archivo no encontrado.', 404);
    }
    header('Content-Type: application/octet-stream');
    header('Content-Disposition: attachment; filename="' . basename($filePath) . '"');
    header('Content-Length: ' . filesize($filePath));
    readfile($filePath);
    exit;
}

if ($action === 'run-analysis') {
    $payload = json_decode(file_get_contents('php://input'), true);
    if (!is_array($payload)) {
        json_error('JSON inválido.', 400);
    }
    $rawFolder = $payload['folder'] ?? '';
    $window = isset($payload['window']) ? $payload['window'] : 10;
    $bandFreqs = $payload['band_freqs'] ?? '63,125,2000';
    $includeSpectrograms = isset($payload['include_spectrograms']) ? (bool) $payload['include_spectrograms'] : true;
    $deviceType = $payload['device_type'] ?? 'auto';

    $folder = normalize_path($rawFolder);
    if (!$folder || !is_allowed_path($folder) || !is_dir($folder)) {
        json_error('Ruta no válida o carpeta no accesible.', 400);
    }

    $window = floatval($window);
    if ($window <= 0) {
        json_error('window debe ser un número positivo.', 400);
    }

    $bandFreqs = trim($bandFreqs);
    if ($bandFreqs === '') {
        $bandFreqs = '63,125,2000';
    }

    $progressFile = get_progress_path($folder);
    file_put_contents($progressFile, "Iniciando análisis...\n");

    $python = 'python3';
    $pythonPath = '/home/quim/.local/lib/python3.10/site-packages';
    $mainScript = escapeshellarg($ROOT . '/audio_analysis/audio_analysis/app/main.py');
    $folderArg = escapeshellarg($folder);
    $windowArg = escapeshellarg((string) $window);
    $bandArg = escapeshellarg($bandFreqs);
    $specArg = $includeSpectrograms ? '--include-spectrograms' : '--no-spectrograms';
    $deviceTypeArg = escapeshellarg($deviceType);

    $cmd = "env PYTHONPATH={$pythonPath}:\$PYTHONPATH $python $mainScript $folderArg --window $windowArg --band-freqs $bandArg $specArg --device-type $deviceTypeArg";

    $descriptors = [
        0 => ['pipe', 'r'],
        1 => ['pipe', 'w'],
        2 => ['pipe', 'w'],
    ];
    $process = proc_open($cmd, $descriptors, $pipes);
    if (!is_resource($process)) {
        json_error('No se pudo iniciar el análisis.', 500);
    }

    fclose($pipes[0]);
    stream_set_blocking($pipes[1], false);
    stream_set_blocking($pipes[2], false);

    $output = [];
    while (true) {
        $read = [$pipes[1], $pipes[2]];
        $write = null;
        $except = null;
        $changed = stream_select($read, $write, $except, 1);
        if ($changed === false) {
            break;
        }
        foreach ($read as $pipe) {
            while (($line = fgets($pipe)) !== false) {
                $trim = trim($line);
                if ($trim === '') {
                    continue;
                }
                $output[] = $trim;
                update_progress($progressFile, $trim);
            }
        }
        $status = proc_get_status($process);
        if (!$status['running']) {
            break;
        }
    }

    fclose($pipes[1]);
    fclose($pipes[2]);
    $returnVar = proc_close($process);

    $completeMessage = $returnVar === 0 ? 'Análisis finalizado.' : 'Análisis finalizado con error.';
    update_progress($progressFile, $completeMessage);

    if ($returnVar !== 0) {
        json_error('Error al ejecutar el análisis: ' . implode("\n", $output), 500);
    }

    $results = list_results($folder);
    $pdfPath = dirname($folder) . DIRECTORY_SEPARATOR . 'resultados' . DIRECTORY_SEPARATOR . 'audio_analysis_report.pdf';
    if (!file_exists($pdfPath)) {
        json_error('El PDF no se generó correctamente.', 500);
    }

    echo json_encode([
        'success' => true,
        'pdf_path' => $pdfPath,
        'results' => $results,
        'output' => $output,
    ]);
    exit;
}

json_error('Action no soportada: ' . $action, 400);
