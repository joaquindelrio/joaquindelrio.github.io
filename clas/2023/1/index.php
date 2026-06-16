<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
$titol = "La Granada 2023";
$logo = "logo.jpg";

?>

<html>
<head>
	<title><?=$titol;?></title>
	<link rel="shortcut icon" href="https://www.sportsform.net/img/icona.ico">
<link rel="apple-touch-icon" href="https://www.sportsform.net/img/apple-touch-icon-57x57-precomposed.png">
<link rel="apple-touch-icon" sizes="72x72" href="https://www.sportsform.net/img/apple-touch-icon-72x72-ipad.png">
<link rel="apple-touch-icon" sizes="114x114" href="https://www.sportsform.net/img/apple-touch-icon-114x114-retina.png">
<link rel="apple-touch-icon" sizes="144x144" href="https://www.sportsform.net/img/apple-touch-icon-144x144-retina.png">
	<style>
body {
	margin-left: 0px;
	margin-top: 0px;
	margin-right: 0px;
	margin-bottom: 0px;
	background-color:#999;
}
body,td,th {
	font-family: Verdana, Geneva, sans-serif;
	font-size: 12px;
	color: #000;
	text-align: center;
}
h2
{
	font-size:17px;
}
a:link {
	color: #333;
}
a:visited {
	color: #333;
}
a:hover {
	color: #333;
}
a:active {
	color: #333;
}
label { width: 12em; float: left; margin-top:8px; font-weight:bold; }
label.error { 

float: none; padding-left: 10em; padding-bottom:-3em; vertical-align:text-top;

position:relative;
color:#F30; font-size:11px;
width:25em;
}
p {
	clear: both;
	text-align: left;
	padding-left:15px;
	vertical-align:baseline;
}
.submit { margin-left: 12em; }
em { font-weight: bold; padding-right: 1em; vertical-align: top; }
.comentari {
	color: #666;
	font-size: 10px;
}
.radio
{
	width:14em;	
}
.radio1
{
	width:auto; margin-left:1.5em; margin-top:0em; margin-bottom:1em;
}
.radio2
{
	width:auto; margin-top:0em;
}
.radiolist
{
	width:16em; margin-left:1.5em; margin-top:1em;
}
.radiolist2
{
	left:14em;
	width:16em; margin-left:1.5em; margin-bottom:1em;
}
.cmxform tr td .demo #formulari fieldset div #internal-source-marker_0.2142485484946519 {
	text-align: left;
}
.nobold {
	font-weight: normal;
}
	</style>
</head>
<body>
	<div style="padding:10px; margin:10px; background-color:white;">
		<?php
if(file_exists($logo))
{
	echo "<img src='$logo'><br><br>";
}
?>
<h3>Resultats <?=$titol;?> </h3>

<p style="text-align: center">
<table style="margin-left:auto;margin-right:auto; border: 1px solid rgba(153, 153, 153, 0.65); padding: 10px;">
<?php
$files = array();
	$dh  = opendir(".");
	while (false !== ($filename = readdir($dh))) {
		if(!in_array($filename, array("index.php",".","..",$logo)))
		{
			if(in_array(pathinfo($filename, PATHINFO_EXTENSION), array("html","htm","pdf"))) {
				$files[] = $filename;
			}
			
			
		}
    		
	}
	asort($files);
	foreach ($files as $filename) {
		echo '<tr>';
			echo '<td style="padding-right:50px; text-align:left; padding-bottom:10px;">';
			echo '<a href="'.$filename.'" target="_blank">'.str_replace(array(".html",".htm",".pdf"),"",$filename).'</a>';
			echo '</td>';
			echo '<td style="padding-bottom:10px;">';
			echo date("d-m-Y H:i", filemtime($filename));
			echo '</td>';
			echo '</tr>';
	}
	
?>
</table>
</p>
<br>
<a href="http://www.sportsform.net" title="Formulari esportiu creat per SPORTS form" style="text-decoration:none;" target="_blank">Formularis esportius:<br><img src="https://www.sportsform.net/img/sportsform.png" title="Formulari esportiu creat per SPORTS form" height="50px" style="margin-top: 10px;"></a>
<br>
<br>
<p style="text-align:center">© 2013-<?=Date("Y");?> :: <a href="http://www.sportsform.net" target="_blank">sportsform.net</a> :: Tots els drets reservats :: <a href="http://www.sportsform.net/forms/termes-condicions.html" target="_blank">Termes i condicions</a></p>
</div>
</body>
</html>
