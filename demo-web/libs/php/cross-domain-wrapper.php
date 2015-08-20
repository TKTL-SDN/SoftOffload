<?php
  header('Content-type: application/json');
  if (isset($_GET['suffix']) {
    $suffix = $_GET['suffix'];
    $url = 'http://127.0.0.1:8080/' + $suffix;
    $json = file_get_contents($url);

    echo $json;
  }
?>