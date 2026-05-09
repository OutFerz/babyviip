/**
 * Script aislado solo para static/pruebas/index.html
 * No usa static/js/home.js ni otros JS del proyecto.
 */
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        var el = document.getElementById("pruebas-footer-year");
        if (el) {
            el.textContent = String(new Date().getFullYear());
        }
    });
})();
