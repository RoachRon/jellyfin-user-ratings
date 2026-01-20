// ---- Paste this into Jellyfin Javascript Injector ----
(() => {
  // Load Updoot JS and config
  const APP_ROOT_PATH = '/updoot'; // Must match your reverse proxy path

  const load = async () => {
    if (document.querySelector('script[data-updoot="1"]')) return;

    try {
      const configUrl = `${window.location.origin}${APP_ROOT_PATH}/assets/config.json`;
      const resp = await fetch(configUrl, { credentials: 'omit' });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

      const cfg = await resp.json();
      const updootSrc = cfg?.updootSrc;
      const adminUserIds = cfg?.adminUserIds;

      if (!updootSrc) throw new Error('Missing updootSrc in config');
      if (!Array.isArray(adminUserIds)) {
        throw new Error('Missing adminUserIds in config');
      }

      // Make runtime config available to updoot.js
      window.UPDOOT_CONFIG = { appRootPath: APP_ROOT_PATH, adminUserIds };

      const s = document.createElement('script');
      s.defer = true;
      s.dataset.updoot = '1';
      s.src = updootSrc;
      s.onerror = (e) => console.error('Failed to load updoot.js', e);
      s.onload = () => console.log('updoot.js loaded');
      (document.head || document.documentElement).appendChild(s);
    } catch (e) {
      console.error('Failed to load Updoot config / script', e);
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', load);
  } else {
    load();
  }

  // Helper required by Updoot
  window.saveJellyfinCredentials = (serverId, accessToken) => {
    const credentials = { Servers: [{ Id: serverId, AccessToken: accessToken }] };
    try {
      localStorage.setItem('jellyfin_credentials', JSON.stringify(credentials));
    } catch (e) {
      console.error('Error saving Jellyfin credentials', e);
    }
  };
})();
