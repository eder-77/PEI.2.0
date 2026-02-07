document.addEventListener("DOMContentLoaded", () => {
  /* =========================================
     1. GESTION DU MENU MOBILE (BURGER)
     ========================================= */
  const burger = document.querySelector(".burger");
  const nav = document.querySelector(".nav-links");

  // On vérifie que les éléments existent avant d'ajouter l'événement
  if (burger && nav) {
    burger.addEventListener("click", () => {
      // Affiche ou cache le menu
      if (nav.style.display === "flex") {
        nav.style.display = "none";
      } else {
        nav.style.display = "flex";
        nav.style.flexDirection = "column";
        nav.style.position = "absolute";
        nav.style.top = "80px";
        nav.style.right = "0";
        nav.style.backgroundColor = "var(--card-bg)"; // Utilise la variable couleur
        nav.style.width = "100%";
        nav.style.padding = "20px";
        nav.style.boxShadow = "var(--shadow)";
        nav.style.zIndex = "999"; // S'assure qu'il est au dessus
      }
    });
  }

  /* =========================================
     2. GESTION DU MODE SOMBRE (DARK MODE)
     ========================================= */
  const themeToggle = document.getElementById("theme-toggle");
  const htmlElement = document.documentElement;

  // Appliquer immédiatement le thème sauvegardé
  const savedTheme = localStorage.getItem("theme") || "light";
  htmlElement.setAttribute("data-theme", savedTheme);

  // Si le bouton existe sur la page actuelle
  if (themeToggle) {
    const icon = themeToggle.querySelector("i");

    // Ajuster l'icône au chargement
    if (savedTheme === "dark" && icon) {
      icon.classList.replace("fa-moon", "fa-sun");
    }

    // Gérer le clic
    themeToggle.addEventListener("click", () => {
      const currentTheme = htmlElement.getAttribute("data-theme");
      const newTheme = currentTheme === "dark" ? "light" : "dark";

      htmlElement.setAttribute("data-theme", newTheme);
      localStorage.setItem("theme", newTheme);

      // Changer l'icône
      if (icon) {
        if (newTheme === "dark") {
          icon.classList.replace("fa-moon", "fa-sun");
        } else {
          icon.classList.replace("fa-sun", "fa-moon");
        }
      }
    });
  }
});
