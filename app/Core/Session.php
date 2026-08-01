<?php

namespace App\Core;

class Session
{

    public static function start()
    {

        if (session_status() == PHP_SESSION_NONE) {

            session_start();

        }

    }

}