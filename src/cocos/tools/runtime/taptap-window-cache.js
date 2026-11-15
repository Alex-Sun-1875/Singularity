'use strict';

// Installed before Cocos copies the platform functions into its mini-game PAL.
// Cocos 3.8.8 reads window information three times per touch event. On TapTap
// iOS each read crosses the synchronous native bridge, even if nothing resized.
// Use the documented getWindowInfo / onWindowResize / onShow contract, leaving
// Cocos screen getters, touch delivery and coordinate conversion unchanged.
const installed = new WeakMap();

function copy(info) {
  const result = Object.assign({}, info);
  if (info.safeArea) result.safeArea = Object.assign({}, info.safeArea);
  return result;
}

function installWindowInfoCache(platform) {
  if (!platform || !['getWindowInfo', 'onWindowResize', 'offWindowResize', 'onShow', 'offShow']
    .every(name => typeof platform[name] === 'function')) return () => {};
  if (installed.has(platform)) return installed.get(platform);
  const original = platform.getWindowInfo;
  const descriptor = Object.getOwnPropertyDescriptor(platform, 'getWindowInfo');
  let snapshot, resizeListening = false, showListening = false, disposed = false;
  const invalidate = () => { snapshot = undefined; };
  const cached = function () {
    // A previously copied Cocos function also becomes a direct delegate after cleanup.
    if (disposed) return original.call(platform);
    if (!snapshot) {
      const value = original.call(platform);
      if (!value || ![value.pixelRatio, value.windowWidth, value.windowHeight]
        .every(n => Number.isFinite(n) && n > 0)) return value;
      snapshot = copy(value);
    }
    // Preserve the API's independently mutable return value, including safeArea.
    return copy(snapshot);
  };
  const cleanup = () => {
    if (disposed) return;
    disposed = true;
    invalidate();
    if (platform.getWindowInfo === cached) {
      if (descriptor) Object.defineProperty(platform, 'getWindowInfo', descriptor);
      else delete platform.getWindowInfo;
    }
    if (resizeListening) { try { platform.offWindowResize(invalidate); } catch (_) {} }
    if (showListening) { try { platform.offShow(invalidate); } catch (_) {} }
    installed.delete(platform);
  };
  try {
    platform.getWindowInfo = cached;
    if (platform.getWindowInfo !== cached) return () => {};
    // Register before Cocos: its resize handler must see the fresh dimensions.
    resizeListening = true;
    platform.onWindowResize(invalidate);
    showListening = true;
    platform.onShow(invalidate);
  } catch (_) {
    cleanup();
    return () => {};
  }
  installed.set(platform, cleanup);
  return cleanup;
}

module.exports = { installWindowInfoCache };
