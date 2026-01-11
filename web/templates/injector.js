// ---- Paste this into Jellyfin Javascript Injector ----
(() => {
    // Helper required by Updoot
    window.saveJellyfinCredentials = (serverId, accessToken) => {
      const credentials = { Servers: [{ Id: serverId, AccessToken: accessToken }] };
      try {
        localStorage.setItem("jellyfin_credentials", JSON.stringify(credentials));
      } catch (e) {
        console.error("Error saving Jellyfin credentials", e);
      }
    };
  
    // Load Updoot JS (once)
    // This file is meant to be COPY/PASTED into the Jellyfin JavaScript Injector plugin.
    // It fetches runtime config (UPDOOT_SRC + VERSION) from the backend, which is driven by Docker env vars.
    const BACKEND_PATH = "/updoot"; // Must match your reverse proxy path

    const load = async () => {
      if (document.querySelector('script[data-tb-updoot="1"]')) return;

      try {
        const configUrl = `${window.location.origin}${BACKEND_PATH}/assets/config.json`;
        const resp = await fetch(configUrl, { credentials: "omit" });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        const cfg = await resp.json();
        const updootSrc = cfg?.updootSrc;
        const version = cfg?.version ?? "1";
        if (!updootSrc) throw new Error("Missing updootSrc in config");

        const s = document.createElement("script");
        s.defer = true;
        s.dataset.tbUpdoot = "1";
        s.src = `${updootSrc}?v=${encodeURIComponent(version)}`;
        s.onerror = (e) => console.error("Failed to load updoot.js", e);
        s.onload = () => console.log("updoot.js loaded");
        (document.head || document.documentElement).appendChild(s);
      } catch (e) {
        console.error("Failed to load Updoot config / script", e);
      }
    };
  
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", load);
    } else {
      load();
    }
  })();
  