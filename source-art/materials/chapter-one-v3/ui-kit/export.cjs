// Original SVG -> PNG only. Reuses the renderer already installed by the Cocos project.
// Run from the repository root: node source-art/materials/chapter-one-v3/ui-kit/export.cjs
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../../../..');
const { Resvg } = require(path.join(root, 'src/cocos/node_modules/@resvg/resvg-js'));
const output = path.join(root, 'assets/materials/chapter-one-v3/ui-kit');
const runtime = path.join(root, 'src/cocos/assets/resources/ui/quiet-bronze');
const syncCocos = process.argv.includes('--sync-cocos');
const skin = JSON.parse(fs.readFileSync(path.join(__dirname, 'skin.source.json'), 'utf8'));
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const alphaResults = [];
const vectors = new Map();
fs.mkdirSync(output, { recursive: true });
for (const asset of skin.assets) {
  const svg = fs.readFileSync(path.join(__dirname, `${asset.id}.svg`));
  const source = svg.toString().match(/<svg\b([^>]*)>([\s\S]*)<\/svg>\s*$/);
  const rootFill = source[1].match(/\bfill="([^"]+)"/);
  vectors.set(asset.id, `<g${rootFill ? ` fill="${rootFill[1]}"` : ''}>${source[2]}</g>`);
  const rendered = new Resvg(svg).render();
  const png = rendered.asPng();
  const actualSize = [png.readUInt32BE(16), png.readUInt32BE(20)];
  if (actualSize.some((v, i) => v !== asset.sourceSizePx[i])) {
    throw new Error(`${asset.id}: actual size ${actualSize} differs from catalog`);
  }
  fs.writeFileSync(path.join(output, `${asset.id}.png`), png);
  asset.sourceSvg = `${skin.sourceDirectory}/${asset.id}.svg`;
  asset.png = `${asset.id}.png`;
  asset.export = {
    actualSizePx: actualSize,
    pngBytes: png.length,
    pngSHA256: hash(png),
    svgSHA256: hash(svg)
  };
  const pixels = rendered.pixels, histogram = new Array(256).fill(0);
  for (let i = 3; i < pixels.length; i += 4) histogram[pixels[i]]++;
  const sample = (x, y) => pixels[(y * rendered.width + x) * 4 + 3];
  const center = sample(Math.floor(rendered.width / 2), Math.floor(rendered.height / 2));
  const min = histogram.findIndex(n => n > 0), max = histogram.findLastIndex(n => n > 0);
  const expectation = asset.alphaExpectation;
  const passed = expectation === 'intentionally-opaque' ? min === 255
    : expectation === 'intentionally-uniform-translucent' ? min > 0 && min === max && max < 255
    : expectation === 'transparent-center-and-exterior' ? sample(0, 0) === 0 && center === 0 && max > 0
    : expectation === 'transparent-exterior-opaque-center' ? sample(0, 0) === 0 && center === 255
    : expectation === 'transparent-exterior-translucent-center' ? sample(0, 0) === 0 && center > 0 && center < 255
    : min === 0 && max > 0;
  if (!passed) throw new Error(`${asset.id}: alpha does not match ${expectation}`);
  alphaResults.push({ id: asset.id, sizePx: actualSize, pngSHA256: hash(png),
    alphaMinMax: [min, max], transparentPixelCount: histogram[0],
    partialPixelCount: histogram.slice(1, 255).reduce((a, b) => a + b, 0), opaquePixelCount: histogram[255],
    alphaSamples: { topLeft: sample(0, 0), center, bottomRight: sample(rendered.width - 1, rendered.height - 1) },
    expectation, passed });
  if (syncCocos) {
    const destination = path.join(runtime, `${asset.id}.png`), metadata = destination + '.meta';
    // Update only established resources, preserving importer settings and UUIDs.
    if (!fs.existsSync(destination) || !fs.existsSync(metadata)) throw new Error(`Missing existing Cocos resource: ${asset.id}`);
    const metadataHash = hash(fs.readFileSync(metadata));
    fs.copyFileSync(path.join(output, `${asset.id}.png`), destination);
    if (hash(fs.readFileSync(destination)) !== hash(png) || hash(fs.readFileSync(metadata)) !== metadataHash)
      throw new Error(`${asset.id}: Cocos synchronization changed metadata or PNG bytes`);
  }
}
fs.writeFileSync(path.join(output, 'skin.json'), JSON.stringify(skin, null, 2) + '\n');
fs.writeFileSync(path.join(output, 'alpha-report.json'), JSON.stringify({
  checked: skin.updated, method: 'Existing resvg RGBA output: complete alpha histogram, representative samples, dimensions and PNG/SVG SHA-256',
  candidateStatus: skin.status, assetCount: skin.assets.length, passedCount: alphaResults.length,
  notEngineValidation: true, cocosPngsSynchronized: syncCocos, results: alphaResults
}, null, 2) + '\n');

// A deterministic source-vector contact sheet. No browser, editor, or game build.
const assetById = new Map(skin.assets.map(asset => [asset.id, asset]));
const art = (id, x, y, w, h) => `<svg x="${x}" y="${y}" width="${w}" height="${h}" viewBox="0 0 ${assetById.get(id).sourceSizePx.join(' ')}" preserveAspectRatio="none">${vectors.get(id)}</svg>`;
function sliced(id, x, y, w, h) {
  const asset = assetById.get(id), [sw, sh] = asset.sourceSizePx;
  const {left: l, right: r, top: t, bottom: b} = asset.insetsPx;
  const sx = [0, l, sw-r], sy = [0, t, sh-b], dx = [x, x+l/2, x+w-r/2], dy = [y, y+t/2, y+h-b/2];
  const widths = [l, sw-l-r, r], heights = [t, sh-t-b, b];
  const targetWidths = [l/2, w-(l+r)/2, r/2], targetHeights = [t/2, h-(t+b)/2, b/2];
  return sy.flatMap((_, row) => sx.map((_, col) => `<svg x="${dx[col]}" y="${dy[row]}" width="${targetWidths[col]}" height="${targetHeights[row]}" viewBox="${sx[col]} ${sy[row]} ${widths[col]} ${heights[row]}" overflow="hidden" preserveAspectRatio="none">${vectors.get(id)}</svg>`)).join('');
}
const text = (x, y, value, color = '#F1F5F5', size = 16) => `<text x="${x}" y="${y}" fill="${color}" font-size="${size}" font-family="Segoe UI, sans-serif">${value}</text>`;
const sheet = [`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="780" viewBox="0 0 1200 780"><rect width="1200" height="780" fill="#100C08"/>`,
  text(40, 48, 'WHITEBRANCH / WARM GOLD &amp; BROWN-BLACK', '#F1F5F5', 28),
  text(40, 77, '17 original vectors · 2 source px = 1 logical px · resource preview, not an engine screenshot', '#B4C5D4', 14),
  text(40, 120, 'BUTTON STATES / SAME BOUNDS', '#B4C5D4', 14)];
['normal', 'hover', 'pressed', 'disabled'].forEach((state, i) => {
  const x = 40 + i * 280;
  sheet.push(sliced(`button-${state}`, x, 138, 240, 56), text(x + 76, 172, 'Continue', state === 'disabled' ? '#8092A5' : '#F1F5F5'), text(x, 219, state, '#B4C5D4', 14));
});
sheet.push(text(40, 267, 'PANEL OVERLAY / PARENT COLOR RETAINED', '#B4C5D4', 14));
[['#221810', 'Panel / brown-black'], ['#110D09', 'Inset / deep black'], ['#5E273C', 'Danger / berry']].forEach(([fill, label], i) => {
  const x = 40 + i * 380;
  sheet.push(`<rect x="${x+2}" y="287" width="356" height="116" fill="${fill}"/>`, sliced('panel-surface', x, 285, 360, 120), sliced('panel-frame', x, 285, 360, 120), text(x + 24, 326, label), text(x + 24, 356, 'Parent fill + 3.5% warm ivory polish', '#B4C5D4', 14));
});
sheet.push(text(40, 451, 'HEALTH / FOCUS / ZERO VALUE', '#B4C5D4', 14));
[['health', .75, 'Health 75 / 100'], ['focus', .42, 'Focus 21 / 50'], ['health', 0, 'Health 0 / 100']].forEach(([kind, value, label], i) => {
  const x = 40 + i * 380;
  sheet.push(text(x, 484, label), sliced('bar-track', x, 500, 320, 16));
  if (value > 0) sheet.push(`<svg x="${x+6}" y="505" width="${308*value}" height="6" viewBox="0 0 ${488*value} 12" preserveAspectRatio="none" overflow="hidden">${vectors.get(`bar-${kind}-fill`)}</svg>`);
  sheet.push(art('bar-cap-left', x, 500, 12, 16), art('bar-cap-right', x+308, 500, 12, 16));
});
sheet.push(text(40, 562, 'SELECTION / ORNAMENT / MASKS / DIVIDERS', '#B4C5D4', 14),
  sliced('button-normal', 40, 581, 224, 48), art('indicator-selected', 52, 589, 12, 32), text(82, 610, 'Selected'),
  art('branch-white-top-left', 300, 579, 84, 84), text(291, 688, 'cool-white branch', '#B4C5D4', 13),
  `<rect x="440" y="589" width="64" height="64" fill="#4598B9"/>`, art('mask-cooldown', 440, 589, 64, 64), text(428, 688, 'cooldown mask', '#B4C5D4', 13),
  sliced('button-normal', 560, 589, 224, 48), sliced('mask-disabled', 560, 589, 224, 48), text(602, 617, 'Content scrim', '#B4C5D4', 14),
  text(579, 688, 'disabled mask', '#B4C5D4', 13), sliced('divider-horizontal', 844, 607, 276, 8), sliced('divider-vertical', 1132, 581, 8, 84),
  text(869, 688, 'honey-gold dividers', '#B4C5D4', 13), text(40, 742, 'Honey-gold / champagne highlights / copper shadows / deep brown-black · geometry, insets and UUIDs retained', '#B4C5D4', 13), '</svg>');
const previewSvg = sheet.join('\n');
fs.writeFileSync(path.join(output, 'ui-kit-preview.svg'), previewSvg);
fs.writeFileSync(path.join(output, 'ui-kit-preview.png'), new Resvg(previewSvg).render().asPng());
fs.writeFileSync(path.join(output, 'preview-report.json'), JSON.stringify({
  checked: skin.updated, renderer: 'existing resvg 2.6.2, static original-vector composition',
  screenshot: 'ui-kit-preview.png', screenshotSizePx: [1200, 780], source: 'ui-kit-preview.svg',
  assetCount: skin.assets.length, cocosPngsSynchronized: syncCocos, notEngineValidation: true,
  checks: ['source dimensions match catalog', 'all alpha expectations pass', 'nine-slice preview retains half-scale source borders', 'parent semantic fills remain visible through low-alpha warm-ivory polish'],
  limits: ['No browser or Cocos build was started.', 'Touch targets and actual game rendering require engine review.']
}, null, 2) + '\n');
console.log(`Exported ${skin.assets.length} original SVGs; alpha ${alphaResults.length}/${skin.assets.length}; contact sheet 1200x780; Cocos sync ${syncCocos ? 'enabled (metadata preserved)' : 'off'}. Existing resvg 2.6.2; no new dependency.`);
