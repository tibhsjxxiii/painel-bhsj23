<?php

namespace App\Core;

use PDO;
use PDOException;

class Database
{

    private static $pdo = null;

    public static function connect()
    {

        if (self::$pdo === null) {

            $config = Config::get('database');

            try {

                self::$pdo = new PDO(

                    "mysql:host={$config['host']};dbname={$config['database']};charset={$config['charset']}",

                    $config['username'],

                    $config['password']

                );

                self::$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

                self::$pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

            } catch (PDOException $e) {

                die("Erro de conexão: " . $e->getMessage());

            }

        }

        return self::$pdo;

    }

}