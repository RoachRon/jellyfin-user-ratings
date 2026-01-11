# jellyfin-updoot (dockerized)

Confirmed working on Jellyfin 10.11.0.

>This project is a fork of the original [jellyfin-updoot](https://github.com/BobHasNoSoul/jellyfin-updoot) project by @BobHasNoSoul, modified to be fully Dockerized and require no modification to the Jellyfin installation.

This is an injection mod for Jellyfin that adds:
- A **thumbs up** “Recommend” button and **comments** section on item pages
- A **recommendations** page
- An **admin** UI (for configured admin user IDs)

The backend is a small Flask service with its own sqlite DB (it does **not** touch Jellyfin's DB).

## Screenshots

![Screenshot 2025-07-04 195513](https://github.com/user-attachments/assets/46b6f059-ae7b-46d7-97c6-528524cfa312)
![Screenshot 2025-07-04 195820](https://github.com/user-attachments/assets/8a28091c-56a7-4b09-8902-f18feb3268ce)
![Screenshot 2025-07-04 195706](https://github.com/user-attachments/assets/f9fa9dd3-5d26-46c6-9e1a-0391237be6cb)
![Screenshot 2025-07-04 195653](https://github.com/user-attachments/assets/74073f5c-642c-4486-a489-b2204f68247f)
![Screenshot 2025-07-04 195551](https://github.com/user-attachments/assets/21dbbd4c-c49e-4131-b9ab-03c16137bb5a)
![Screenshot 2025-07-04 195529](https://github.com/user-attachments/assets/0815cec9-ad8b-444f-8e0e-1bf6b7e08c15)

## How it works

- You run this repo as a Docker container.
- Your reverse proxy routes Jellyfin requests for `/updoot/*` to that container.
- In Jellyfin, you inject `injector.js` using the [Jellyfin JavaScript](https://github.com/n00bcodr/Jellyfin-JavaScript-Injector) injector plugin.
- `injector.js` loads `updoot.js` (with a cache-busting `VERSION`) and the UI appears in Jellyfin.

## Installation (recommended)

### 1) Run the backend (Docker)

The only required Docker configuration is:
- **env vars**
- a **volume mount** for the sqlite DB (defaults to `/data/recommendations.db`)

This repo includes a sample `docker-compose.yml`:

```bash
docker compose up -d --build
```

### 2) Reverse proxy `/updoot/*` to the container

Example Nginx snippet (Jellyfin vhost):

```
# Proxy to Updoot backend
location /updoot/ {
    proxy_pass http://YOURSERVERIP:8099/updoot/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $http_host;
}
```

### 3) Inject the frontend loader with the Jellyfin JavaScript Injector plugin

Install the Jellyfin JavaScript Injector plugin:
`https://github.com/n00bcodr/Jellyfin-JavaScript-Injector`

In the plugin config, create a new script and copy/paste the contents of `web/templates/injector.js`.

**Note:** This `injector.js` is not the main UI script. It's a small loader that runs in the Jellyfin frontend, fetches `/updoot/assets/config.json`, then loads `updoot.js`.

### 4) Clear cache + reload

If clients aren't picking up changes, bump `VERSION` (env var) and reload.

## Configuration (env vars)

All configuration is via env vars (no manual edits required).

### Backend

- **`JELLYFIN_URL`**: Base URL to your Jellyfin server (used for username lookups)
- **`JELLYFIN_API_KEY`**: Jellyfin API key (used for username lookups)
- **`ADMIN_USER_IDS`**: Comma-separated Jellyfin user IDs that can access admin UI
- **`BACKEND_PORT`**: Port to run the backend on. Default: `8099`
- **`DB_PATH`**: Path to sqlite DB inside the container. Default: `/data/recommendations.db`
- **`LOG_LEVEL`**: Default: `INFO`

### Frontend / injection

- **`BACKEND_PATH`**: Path where the backend is reverse-proxied under Jellyfin. Default: `/updoot`
- **`BACKEND_URL`**: (Optional) Absolute URL override for the backend (rarely needed)
- **`SERVER_URL_FALLBACK`**: (Optional) Used only if Jellyfin credentials are missing in localStorage
- **`UPDOOT_SRC`**: URL that the *pasted injector snippet* should load for `updoot.js`. Served via `/updoot/assets/config.json`. Default: `/updoot/assets/updoot.js`
- **`CACHE_VERSION`**: Cache-busting version string used by the *pasted injector snippet* when loading `updoot.js`. Served via `/updoot/assets/config.json`. Default: `1`

## Dev / local run (no Docker)

```bash
pip install -r requirements.txt
PYTHONPATH=./src python -m updoot_service
```

## FAQ

- **can this run on truenas?**: no clue i dont have it but if you can run terminal and python then you should be able to do this but im not 100% sure on each specific setup so again give it a try but if you are unsure google for a guide for running python on your system and basic file editing inside of docker terminals would be the place to start before opening an issue.
- **does this work on mobile?**: yes it works just fine on mobile and xbox and pc etc this is a jellyfin-web injection mod.
- **will this survive a jellyfin update?**: usually yes. since injection is done via the JavaScript injector plugin, you generally won't need to re-edit `index.html` after updates.
- **do i mind pull requests?**: i dont mind but please try to make it clear what the pull request is for before hiting submit (most of the time im doing things like this in my free time for my own server but i like to share with the community so usually check github every few days or when im about to go to sleep so wont really be instantly responding)
- **would i make this into a plugin?**: yes if someone can show me the docs required to build via a headless linux environment. i cant build with windows (i know that is weird but trust me my setup wont play nice with it)
- **can anyone turn this into a plugin?**: sure its open source and if you can then do so, just please link back to the original somewhere in the description and im fine with it.
- **can we donate?**: sure thing thank you https://ko-fi.com/bobhasnosoul

