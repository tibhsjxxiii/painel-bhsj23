<?php

require_once 'config/environment.php';

require_once APP_PATH . '/Core/Autoload.php';

use App\Core\Config;
use App\Core\Database;
use App\Core\Session;

Session::start();

$app = Config::get('app');

$db = Database::connect();

?>

<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<title><?= $app['name']; ?></title>

<style>

body{

background:#0F172A;

color:white;

font-family:Segoe UI;

display:flex;

justify-content:center;

align-items:center;

height:100vh;

margin:0;

}

.card{

width:700px;

background:#1E293B;

padding:40px;

border-radius:15px;

box-shadow:0 0 30px rgba(0,0,0,.3);

}

h1{

margin-top:0;

}

.ok{

color:#10B981;

font-size:20px;

}

</style>

</head>

<body>

<div class="card">

<h1><?= $app['hospital']; ?></h1>

<p class="ok">✔ Fundação do sistema iniciada com sucesso.</p>

<hr>

<p><b>Sistema:</b> <?= $app['name']; ?></p>

<p><b>Versão:</b> <?= $app['version']; ?></p>

<p><b>Banco:</b> Conectado com sucesso.</p>

<p><b>Ambiente:</b> <?= APP_ENV; ?></p>

<p><b>Idioma:</b> <?= $app['language']; ?></p>

<p><b>Timezone:</b> <?= $app['timezone']; ?></p>

</div>

</body>

</html>