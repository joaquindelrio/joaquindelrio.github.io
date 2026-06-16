<?php
header("Content-Type: text/plain; charset=utf-8");
$cmd = "bash /home/quim/www/clas/update_historico.sh 2>&1";
passthru($cmd, $ret);
echo "\nRET=$ret\n";
