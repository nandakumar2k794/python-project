const waitForCivic = (attempts = 50) =>
  new Promise((resolve, reject) => {
    const check = () => {
      if (window.Civic?.API) {
        resolve(window.Civic);
        return;
      }

      if (attempts <= 0) {
        reject(new Error("App client failed to initialize"));
        return;
      }

      attempts -= 1;
      window.setTimeout(check, 100);
    };

    check();
  });

const initCitizenMap = async () => {
  if (!document.getElementById("map")) return;

  try {
    const mapEl = document.getElementById("map");
    const civic = await waitForCivic();
    const map = L.map(mapEl).setView([12.9716, 77.5946], 12);
    const createFallbackHeatLayer = (points) =>
      L.featureGroup(
        points.map(([lat, lng, intensity]) =>
          L.circleMarker([lat, lng], {
            radius: Math.max(14, Math.round(28 * intensity)),
            stroke: false,
            fillColor: intensity > 0.75 ? "#ef4444" : intensity > 0.5 ? "#f59e0b" : "#22c55e",
            fillOpacity: Math.min(0.45, 0.18 + intensity * 0.22),
            className: "fallback-heat-point",
          })
        )
      );

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors",
      className: "map-tile",
      userAgent: "CivicReport/1.0 (+http://localhost)",
    }).addTo(map);

    const defaultIcon = L.icon({
      iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2300C896"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>',
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32],
    });

    const statusIcons = {
      Submitted: L.icon({
        iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%235BA3D0"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>',
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32],
      }),
      "In Progress": L.icon({
        iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23FCD34D"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>',
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32],
      }),
      Resolved: L.icon({
        iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2300C896"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>',
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32],
      }),
    };

    const userMarker = L.marker([12.9716, 77.5946], { icon: defaultIcon }).addTo(map);
    userMarker.bindPopup(
      "<div style='padding:8px;color:#E6EDF3'><b>Your Location</b></div>",
      { closeButton: false }
    );

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        map.setView([lat, lng], 14);
        userMarker.setLatLng([lat, lng]);
        userMarker.setPopupContent(
          `<div style='padding:8px;color:#E6EDF3'><b>Current Location</b><br><small>${lat.toFixed(4)}, ${lng.toFixed(4)}</small></div>`
        );
      },
      (error) => console.log("Geolocation error:", error),
      { enableHighAccuracy: true, timeout: 5000 }
    );

    const markersGroup = L.featureGroup().addTo(map);
    let heatmapLayer = null;
    let showingHeatmap = false;
    const heatmapBtn = document.getElementById("toggle-heatmap");

    const setHeatmapButtonState = (enabled, label = "Show Heatmap") => {
      if (!heatmapBtn) return;
      heatmapBtn.disabled = !enabled;
      heatmapBtn.textContent = label;
      heatmapBtn.classList.toggle("opacity-50", !enabled);
      heatmapBtn.classList.toggle("cursor-not-allowed", !enabled);
    };

    setHeatmapButtonState(false, "Loading heatmap...");

    if (heatmapBtn) {
      heatmapBtn.addEventListener("click", () => {
        if (!heatmapLayer) {
          if (civic?.toast) {
            civic.toast("No heatmap data available yet", "err", 2500);
          }
          return;
        }

        if (showingHeatmap) {
          if (!map.hasLayer(markersGroup)) {
            markersGroup.addTo(map);
          }
          if (map.hasLayer(heatmapLayer)) {
            map.removeLayer(heatmapLayer);
          }
          setHeatmapButtonState(true, "Show Heatmap");
          heatmapBtn.style.background = "linear-gradient(to right, rgb(34, 211, 238), rgb(59, 130, 246))";
          showingHeatmap = false;
        } else {
          if (map.hasLayer(markersGroup)) {
            map.removeLayer(markersGroup);
          }
          heatmapLayer.addTo(map);
          setHeatmapButtonState(true, "Show Markers");
          heatmapBtn.style.background = "linear-gradient(to right, rgb(59, 130, 246), rgb(139, 92, 246))";
          showingHeatmap = true;
        }
      });
    }

    const renderMapError = (message) => {
      console.error("Map data error:", message);
      if (!document.getElementById("map-error")) {
        const msg = document.createElement("div");
        msg.id = "map-error";
        msg.style.cssText =
          "position:absolute;top:10px;left:10px;background:rgba(255,107,53,.1);border:1px solid #FF6B35;color:#ff7f66;padding:12px;border-radius:6px;font-size:12px;z-index:1000";
        msg.textContent = message;
        mapEl.appendChild(msg);
      }
    };

    const loadIssues = async () => {
      try {
        const response = await civic.API.req("/api/issues/?page_size=500");
        const issues = response.results || response || [];

        if (!Array.isArray(issues)) {
          throw new Error("Invalid issue data format");
        }

        const heatData = [];
        let loaded = 0;

        issues.forEach((issue) => {
          try {
            const lat = Number(issue?.location?.lat || 0);
            const lng = Number(issue?.location?.lng || 0);
            if (!lat || !lng) return;

            const status = issue.status || "Submitted";
            const icon = statusIcons[status] || defaultIcon;
            const marker = L.marker([lat, lng], { icon });
            const popup = `<div style='padding:8px;color:#E6EDF3;font-size:12px'><b>${civic.escapeHtml(issue.issue_code || "Issue")}</b><br><strong>${civic.escapeHtml(issue.title || "No Title")}</strong><br><small>Status: ${civic.escapeHtml(status)}</small><br><small>Category: ${civic.escapeHtml(issue.category || "Unknown")}</small></div>`;

            marker.bindPopup(popup);
            markersGroup.addLayer(marker);
            heatData.push([lat, lng, 0.6]);
            loaded += 1;
          } catch (error) {
            console.error("Marker error:", error);
          }
        });

        if (heatData.length > 0) {
          if (typeof L.heatLayer === "function") {
            heatmapLayer = L.heatLayer(heatData, {
              radius: 30,
              blur: 25,
              maxZoom: 15,
              gradient: { 0.0: "#0000FF", 0.33: "#00FF00", 0.66: "#FFFF00", 1.0: "#FF0000" },
            });
          } else {
            heatmapLayer = createFallbackHeatLayer(heatData);
            console.warn("leaflet.heat plugin did not load; using fallback heat layer");
          }
          setHeatmapButtonState(true, "Show Heatmap");
        } else if (heatData.length === 0) {
          setHeatmapButtonState(false, "No heatmap data");
        }

        if (loaded > 0) {
          console.log(`Loaded ${loaded} issue markers for map`);
        } else {
          renderMapError("No issue locations available to plot on the map");
        }
      } catch (error) {
        setHeatmapButtonState(false, "Heatmap unavailable");
        renderMapError(`Unable to load issues: ${error.message || "Unknown error"}`);
      }
    };

    loadIssues();

    map.on("popupopen", (event) => {
      const popup = event.popup;
      if (popup?._container) {
        popup._container.style.animation = "slideUp 300ms ease-out";
      }
    });

    map.on("tileerror", (event) => {
      console.error("Map tile failed to load:", event.url);
      console.error("Tile coords:", event.coords);
    });
  } catch (error) {
    console.error("Map initialization error:", error);
    const el = document.getElementById("map");
    if (el) {
      el.innerHTML =
        "<div style='display:flex;align-items:center;justify-content:center;height:100%;color:#93a4b8'>Map failed to load</div>";
    }
  }
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initCitizenMap);
} else {
  initCitizenMap();
}
