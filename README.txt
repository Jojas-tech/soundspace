SOUND SPACE — RECOVERY + FEATURE BUILD (PATCHED)

WHAT'S INCLUDED
- Faster Python launcher that checks the existing local server and opens the app automatically.
- Same original address: http://localhost:8000/Soundspace.html
- YouTube search supports up to 50 results per request and a Load more results button (uses YouTube page tokens).
- LRCLIB lookup tries cleaned/exact title and artist variants, ranks multiple matches and prefers synced lyrics.
- A dedicated “♫ Lyrics Studio” page is available directly from the left sidebar; it is separate from Customize.
- Times New Roman is available in the whole-app font dropdown and the Lyrics Studio lyrics-font dropdown.
- The standalone Lyrics Studio includes an app-wide font selector, lyrics font/size/colour/opacity controls, surrounding-line settings, bold active line, live preview, import and paste/edit actions.
- Existing local audio import, IndexedDB storage, local playlists, favorites, lyric import/paste, lyric downloads and local audio export are retained.
- Discover Quick Picks and Recently Played are based on the play counts and timestamps already stored in this browser.

INSTALL
1. Extract the entire ZIP into a normal folder.
2. Open youtube_key.txt and paste a NEW YouTube Data API v3 key. Do not share this file.
3. Save it, then double-click Start_SoundSpace.bat.
4. The launcher opens http://localhost:8000/Soundspace.html automatically.
5. Keep the server console open while using Sound Space.

IMPORTANT DATA PRESERVATION
- Keep the exact localhost:8000 address. Do not switch to 127.0.0.1, file://, another port, or clear browser site data.
- Your current IndexedDB library is tied to the origin http://localhost:8000. This update does not delete or migrate it.
- Imported audio and lyrics stay in this browser's local storage. Back up important audio files and export the library metadata backup in Settings.

OFFLINE USE
- Imported local audio and its saved lyrics can play without internet, provided the browser can still access the app at localhost:8000 and the browser has retained its stored data.
- YouTube search/streaming and LRCLIB lookups require internet.
- This is not an offline YouTube downloader. The app only exports local audio files that you imported and are authorised to store.
- Browser storage can be cleared or evicted; keep original files and backups.

SECURITY
- The previously embedded API key has been removed from this build. Rotate that exposed key in Google Cloud Console and use a fresh key in youtube_key.txt.
- Restrict the new key to YouTube Data API v3. Keep youtube_key.txt private and out of shared folders/repos.

KNOWN LIMITS / NEXT PASS
- Android PWA packaging, a full offline service-worker install flow, more advanced recommendation controls and broader device-to-device sync still need a dedicated implementation/test pass.
- Karaoke word-by-word highlighting requires word-level timestamps; ordinary LRC files are line-synced.
- YouTube videos that block embedding remain unplayable inside the embedded player.

DISCOVER
- Quick Picks and the Daily Mix are generated from local play counts and last-played timestamps.
- History shows locally stored recently played tracks. These are not uploaded or synced to another device.


LATEST BUILD — V3 (31 October 2026)
- Lyrics Studio is now a dedicated page in the left navigation. It is no longer a section buried inside Customize.
- The dedicated page has its own lyrics preview, lyrics font controls, and app-wide font control.
- Times New Roman is selectable for both the whole app and the lyrics display.
- Lyrics appearance changes save to this browser and apply to the right-side lyrics panel.
- Import .LRC/.TXT and paste/edit actions are available from the Lyrics Studio page when a track is selected.
- The launcher checks a V3-specific server build marker and will not silently reuse an older Sound Space server on port 8000.

To update: close old Sound Space server windows, extract this ZIP into a NEW folder, then run Start_SoundSpace.bat. Existing browser data remains on the same localhost origin.


ANDROID PWA (installable app)  — added in the PWA build
WHAT CHANGED
- Soundspace.html is the file you supplied, with only PWA tags added to <head> (manifest, theme colour, icons, pwa.js).
- New files: manifest.webmanifest, sw.js (offline app shell), pwa.js, index.html, icons/.
- All existing features are unchanged: local audio import, IndexedDB library, playlists, favorites, synced lyrics, Lyrics Studio, fonts, backups, YouTube search/embedded playback, LRCLIB lookup.

WHY A PHONE CAN'T JUST USE THE PC'S localhost
Chrome on Android only installs and runs service workers from HTTPS (or the phone's own localhost). Python/Start_SoundSpace.bat keeps working on a PC exactly as before, but for the phone, host this folder on any free HTTPS static host:
  1. Upload the whole folder (keep file names) to e.g. Cloudflare Pages, Netlify Drop (app.netlify.com/drop), GitHub Pages or Firebase Hosting.
  2. On the Android phone open  https://YOUR-SITE/Soundspace.html  in Chrome.
  3. Tap the "Install SoundSpace" pill, or Chrome menu (⋮) → Add to Home screen / Install app.
  4. Launch it from the home screen: it opens full-screen and the app shell works offline.

NO PYTHON SERVER NEEDED ON THE PHONE
- Lyrics lookup: if /api/lyrics is not available, pwa.js asks LRCLIB directly from the phone (same matching/ranking as the server).
- YouTube search: if /api/youtube is not available, the app asks once for your own YouTube Data API v3 key (or use Settings → "Set YouTube key on this device"). The key stays in that browser and is sent only to Google. In Google Cloud Console restrict it to YouTube Data API v3 AND to your site's web address (HTTP referrer) so nobody can reuse it. Do not put a key in any file you upload to a public host.
- If the Python server IS reachable at the same address, it is used first, exactly as before.

IMPORTANT ON PHONE DATA
- Browser storage is per address. The phone app has its own empty library; your PC library on http://localhost:8000 is not copied. Import songs on the phone (Import music → pick files), or restore from a metadata backup (audio is not included in backups).
- Android may clear site data if storage is low. Keep original files. In Chrome → Site settings you can allow persistent storage by installing the app (installed apps are far less likely to be evicted).
- Offline: imported audio, saved lyrics, playlists and settings work without internet. YouTube search/playback and online lyrics lookup need internet.
- Updating: upload the new files and bump "soundspace-shell-v1" in sw.js (e.g. -v2) so phones fetch the new version.
