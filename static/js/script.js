/*
 * ITR Learn & Simulate
 * static/js/script.js
 * Shared UI helpers and navigation logic
 */

"use strict";


/* =========================================
   DROPDOWN MENUS
   Open/close nav dropdown menus
========================================= */

document
    .querySelectorAll(".dropdown-button")
    .forEach(function(button) {

        button.addEventListener("click", function () {

            const menu = this.nextElementSibling;

            // Close other open dropdowns
            document
                .querySelectorAll(".dropdown-menu")
                .forEach(function(item) {
                    if (item !== menu) {
                        item.classList.remove("show");
                    }
                });

            // Toggle this dropdown
            menu.classList.toggle("show");
        });
    });


/* Close dropdown on outside click */

document.addEventListener("click", function(event) {

    if (!event.target.closest(".nav-dropdown")) {
        document
            .querySelectorAll(".dropdown-menu")
            .forEach(function(menu) {
                menu.classList.remove("show");
            });
    }
});


/* =========================================
   MOBILE NAVIGATION TOGGLE
========================================= */

const mobileToggle = document.getElementById("mobileNavToggle");
const navLinks = document.getElementById("navLinks");

if (mobileToggle && navLinks) {
    mobileToggle.addEventListener("click", function() {
        navLinks.classList.toggle("mobile-open");
        mobileToggle.textContent = navLinks.classList.contains("mobile-open") ? "✕" : "☰";
    });
}


/* =========================================
   FLASH MESSAGE AUTO-DISMISS
   Auto-hide flash messages after 5 seconds
========================================= */

setTimeout(function() {
    document.querySelectorAll(".flash").forEach(function(el) {
        el.style.transition = "opacity 0.5s";
        el.style.opacity = "0";
        setTimeout(function() {
            el.remove();
        }, 500);
    });
}, 5000);


/* =========================================
   FORMAT CURRENCY INPUT
   Add ₹ indicator to number inputs on blur
========================================= */

document.querySelectorAll('input[type="number"]').forEach(function(input) {
    input.addEventListener("blur", function() {
        if (this.value < 0) {
            this.value = 0;
        }
    });
});


/* =========================================
   ACTIVE NAV ITEM HIGHLIGHTING
========================================= */

(function() {
    const currentPath = window.location.pathname;
    document.querySelectorAll(".nav-item").forEach(function(link) {
        if (link.href && link.href.includes(currentPath) && currentPath !== "/") {
            link.classList.add("active");
        }
    });
})();


/* =========================================
   TRAINING LESSON — MARK COMPLETE BUTTON
========================================= */

const completeForm = document.getElementById("completeLessonForm");
if (completeForm) {
    completeForm.addEventListener("submit", function(e) {
        const btn = completeForm.querySelector("button[type='submit']");
        if (btn) {
            btn.disabled = true;
            btn.textContent = "Saving...";
        }
    });
}


/* =========================================
   SIMULATION STEP — FORM VALIDATION
========================================= */

const simForm = document.getElementById("simulationStepForm");
if (simForm) {
    simForm.addEventListener("submit", function(e) {
        // Client-side required field check
        let valid = true;
        simForm.querySelectorAll("[required]").forEach(function(input) {
            if (!input.value.trim()) {
                input.classList.add("input-error");
                valid = false;
            } else {
                input.classList.remove("input-error");
            }
        });

        if (!valid) {
            e.preventDefault();
            const errorBanner = document.getElementById("formErrorBanner");
            if (errorBanner) {
                errorBanner.style.display = "block";
            }
        }
    });
}


/* =========================================
   NUMBER FORMATTER UTILITY
========================================= */

function formatINR(amount) {
    if (isNaN(amount)) return "₹0";
    return "₹" + parseFloat(amount).toLocaleString("en-IN", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}
