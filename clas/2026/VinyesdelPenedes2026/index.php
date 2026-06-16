<?php
$directory = '.'; // Cambia esto si necesitas listar otra carpeta

// Obtener la lista de directorios
$dirs = array_filter(glob($directory . '/*'), 'is_dir');

?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Curses</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 20px;
        }
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            margin: 5px 0;
        }
        a {
            text-decoration: none;
            color: blue;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <h2>Curses></h2>
    <ul>
        <?php if (!empty($dirs)): ?>
            <?php foreach ($dirs as $dir): ?>
                <li><a href="<?php echo basename($dir); ?>"><?php echo basename($dir); ?></a></li>
            <?php endforeach; ?>
        <?php else: ?>
            <li>No hay directorios disponibles.</li>
        <?php endif; ?>
    </ul>
</body>
</html>