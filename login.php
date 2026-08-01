<?php

require_once 'config/environment.php';

require_once APP_PATH.'/Core/Autoload.php';

use App\Core\Config;

$app=Config::get('app');

?>

<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<title>Login</title>

<link rel="stylesheet" href="assets/css/reset.css">

<link rel="stylesheet" href="assets/css/variables.css">

<link rel="stylesheet" href="assets/css/theme-dark.css">

<link rel="stylesheet" href="assets/css/login.css">

</head>

<body>

<div class="container">

<div class="login-card">

<img src="assets/images/logo.png" class="logo">

<div class="title">

<?= $app['hospital']; ?>

</div>

<div class="subtitle">

Painel Estratégico

</div>

<form>

<label>Usuário</label>

<input
type="text"
placeholder="Digite seu usuário">

<label>Senha</label>

<input
type="password"
placeholder="Digite sua senha">

<button>

Entrar

</button>

</form>

<div class="footer">

Versão <?= $app['version']; ?>

<br><br>

BHSJ23 Intelligence Platform

</div>

</div>

</div>

</body>

</html>