<?php
header("Content-Type: text/plain; charset=utf-8");
echo "whoami: "; system("whoami");
echo "\nls historico:\n";
system("ls -la /home/quim/www/clas/historico 2>&1");
?>
