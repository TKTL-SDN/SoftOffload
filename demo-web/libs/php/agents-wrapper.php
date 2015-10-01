<?php
  header('Content-type: application/json');
  $url = 'http://127.0.0.1:8080/wm/softoffload/agents/json';
  $json = file_get_contents($url);

  echo $json;
?>
