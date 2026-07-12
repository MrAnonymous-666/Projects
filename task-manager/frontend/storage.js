// ===== UNIFIED DEVICE STORAGE ADAPTER =====
// This is what makes the app "use device storage" properly on every platform:
//
// - Android / iOS (packaged with Capacitor): uses the native Preferences
//   plugin, which stores data in Android's SharedPreferences / iOS's
//   UserDefaults. This is the OS's own persistent storage - the same
//   mechanism every native app uses for settings/small data. It survives
//   restarts, force-closes, and is NOT cleared by "clear browser cache"
//   style actions the way a WebView's localStorage sometimes can be.
//
// - Windows/Mac/Linux (Electron) and plain web/PWA: uses the browser's
//   localStorage, which already persists across restarts and shutdowns
//   (see earlier explanation - this was never actually the weak point).
//
// Your app code below never touches localStorage or Preferences directly -
// it only calls deviceStorage.get/set/remove, so the correct backend is
// used automatically depending on what the app is running on.

const deviceStorage = {
  isNative() {
    return !!(window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.Preferences);
  },

  async get(key) {
    if (this.isNative()) {
      const { value } = await window.Capacitor.Plugins.Preferences.get({ key });
      return value;
    }
    return localStorage.getItem(key);
  },

  async set(key, value) {
    if (this.isNative()) {
      await window.Capacitor.Plugins.Preferences.set({ key, value });
    } else {
      localStorage.setItem(key, value);
    }
  },

  async remove(key) {
    if (this.isNative()) {
      await window.Capacitor.Plugins.Preferences.remove({ key });
    } else {
      localStorage.removeItem(key);
    }
  }
};
