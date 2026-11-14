// Project startup adapter for Cocos Creator 3.8.8's firstScreen interface.
// Keep its WebGL 2 context setup; the game's LoadingScreen owns the visible UI.
// https://docs.cocos.com/creator/3.8/manual/en/editor/publish/custom-project-build-template.html
function start(alpha, antialias, useWebgl2) {
    if (useWebgl2 !== 'true') {
        return Promise.reject(new Error('Startup requires the configured WebGL 2 backend.'));
    }
    const gl = window.canvas.getContext('webgl2', {
        alpha: alpha === 'true',
        antialias: antialias !== 'false',
        depth: true,
        stencil: true,
        premultipliedAlpha: false,
        preserveDrawingBuffer: false,
        powerPreference: 'default',
        failIfMajorPerformanceCaveat: false,
    });
    if (!gl) {
        return Promise.reject(new Error('WebGL 2 is unavailable during game startup.'));
    }
    // The official first screen publishes this capability for the engine adapter.
    window.WebGL2RenderingContext = true;
    gl.clearColor(0.01568627450980392, 0.03529411764705882, 0.0392156862745098, 1);
    gl.clear(gl.COLOR_BUFFER_BIT);
    return Promise.resolve();
}

// Preserve the generated game.js promise chain without a separate splash or RAF loop.
function setProgress() {
    return Promise.resolve();
}

module.exports = {start, setProgress, end: setProgress};
