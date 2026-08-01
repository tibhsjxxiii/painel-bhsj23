<?php

namespace App\Core;

class Config
{

    public static function get($arquivo)
    {
        return require CONFIG_PATH . '/' . $arquivo . '.php';
    }

}