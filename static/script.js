document.addEventListener("DOMContentLoaded", () => {
  // 🔁 Titre cliquable → refresh
  const titleHeading = document.querySelector("header h1");
  if (titleHeading) {
    titleHeading.style.cursor = "pointer";
    titleHeading.addEventListener("click", () => window.location.reload());
  }

  // 📥 Gestion du menu de sélection de jeu
  const jeuSelect = document.getElementById("jeuSelect");
  const downloadLinks = document.querySelector(".download-links");
  const downloadSelect = document.getElementById("downloadSelect");

  if (downloadLinks) downloadLinks.style.display = "none";

  if (jeuSelect) {
    jeuSelect.addEventListener("change", () => {
      if (jeuSelect.value) {
        if (downloadLinks) downloadLinks.style.display = "flex";
      } else {
        if (downloadLinks) downloadLinks.style.display = "none";
      }
    });
  }

  // 📎 Menu déroulant pour téléchargements auto
  if (downloadSelect) {
    downloadSelect.addEventListener("change", (e) => {
      const url = e.target.value;
      if (url) {
        window.open(url, '_blank');
        e.target.selectedIndex = 0; // reset la sélection
      }
    });
  }

  // 📤 Formulaire d’envoi
  const form = document.getElementById("uploadForm");
  const fileInput = document.getElementById("csvFile");
  const messageDiv = document.getElementById("message");
  const rapportPre = document.getElementById("rapport");
  const loadingContainer = document.getElementById("loading-container");
  const loadingBar = document.getElementById("loading-bar");
  const heatmapContainer = document.getElementById("heatmap-container");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const file = fileInput.files[0];
    if (!file) {
      messageDiv.textContent = "❌ Aucun fichier sélectionné.";
      return;
    }

    // ⏳ Reset affichage
    loadingContainer.style.display = "block";
    loadingBar.style.width = "0%";
    messageDiv.textContent = "⏳ Analyse en cours...";
    rapportPre.textContent = "";
    heatmapContainer.style.display = "none";
    heatmapContainer.innerHTML = "";

    const formData = new FormData();
    formData.append("csv", file);
    formData.append("jeu", jeuSelect.value);

    try {
      let progress = 0;
      const interval = setInterval(() => {
        progress += 10;
        if (progress <= 90) {
          loadingBar.style.width = progress + "%";
        } else {
          clearInterval(interval);
        }
      }, 200);

      const response = await fetch("/upload", {
        method: "POST",
        body: formData
      });

      clearInterval(interval);
      loadingBar.style.width = "100%";

      const data = await response.json();

      if (data.success) {
        messageDiv.textContent = "✅ Analyse terminée avec succès !";

        rapportPre.textContent = data.rapport || "Aucun rapport généré.";

        if (data.heatmap_boules) {
          heatmapContainer.style.display = "block";
          heatmapContainer.innerHTML = "<h3>🔥 Heatmap Boules :</h3>";
          const img = document.createElement("img");
          img.src = data.heatmap_boules;
          img.alt = "Heatmap boules";
          img.classList.add("img-fluid", "mb-3");
          heatmapContainer.appendChild(img);
        }

        if (data.heatmap_chances) {
          const img = document.createElement("img");
          img.src = data.heatmap_chances;
          img.alt = "Heatmap chances";
          img.classList.add("img-fluid", "mb-3");
          heatmapContainer.appendChild(img);
        }

      } else {
        messageDiv.textContent = `❌ Erreur : ${data.message}`;
      }
    } catch (err) {
      messageDiv.textContent = "❌ Erreur lors de l'analyse.";
      console.error(err);
    } finally {
      setTimeout(() => {
        loadingContainer.style.display = "none";
        loadingBar.style.width = "0%";
      }, 1000);
    }
  });
});