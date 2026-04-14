/**
 * ventas.js — Página ventas y clientes (resumen público).
 * Plantilla: templates/ventas.html
 */
(function () {
    "use strict";
    document.addEventListener("DOMContentLoaded", function () {
        var y = document.getElementById("footer-year");
        if (y) y.textContent = String(new Date().getFullYear());
    });
})();
