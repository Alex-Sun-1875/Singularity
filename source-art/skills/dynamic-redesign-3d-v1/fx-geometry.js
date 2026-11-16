import * as THREE from 'three';

// Design-preview geometry only. Materials own no textures: callers may dispose
// every returned geometry/material after a frame while retaining shared maps.
const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
const finite = (x, fallback) => Number.isFinite(x) ? x : fallback;
const mix = (a, b, t) => a + (b - a) * t;
const smooth = t => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };

function bandGeometry(radius, from, to, width, radialOffset = 0, y = 0, steps = 48) {
  const positions = [], uv = [], indices = [];
  for (let i = 0; i <= steps; i++) {
    const u = i / steps;
    const angle = mix(from, to, u);
    // The tail feathers out while the cutting head remains readable; the texture
    // provides the razor point and real transparent slits rather than a white fill.
    const taper = Math.max(.045, Math.pow(Math.sin(Math.PI * u), .42));
    const w = width * taper;
    const inner = radius + radialOffset - w * .52;
    const outer = radius + radialOffset + w * .48;
    const c = Math.cos(angle), s = Math.sin(angle);
    const lift = Math.sin(u * Math.PI) * width * .055;
    positions.push(inner * c, y + lift, inner * s, outer * c, y + lift, outer * s);
    // Ribbon PNG's dark upper spine maps inboard, lower bright edge outboard.
    // Trim only empty top/bottom UV margins, retaining its generated alpha holes.
    uv.push(u, .84, u, .16);
    if (i < steps) {
      const a = i * 2;
      indices.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  geometry.computeBoundingSphere();
  return geometry;
}

function bladeEdgeCurve(radius, from, to, width, firstFraction, y = 0, steps = 28) {
  const points = [];
  for (let i = 0; i <= steps; i++) {
    const u = mix(firstFraction, 1, i / steps);
    const a = mix(from, to, u);
    const taper = Math.max(.045, Math.pow(Math.sin(Math.PI * u), .42));
    const r = radius + width * .27 * taper;
    points.push(new THREE.Vector3(r * Math.cos(a), y, r * Math.sin(a)));
  }
  return new THREE.CatmullRomCurve3(points, false, 'centripetal');
}

function tube(group, curve, radius, color, opacity, segments = 40, additive = false) {
  if (radius <= 0 || opacity <= .001) return;
  const geometry = new THREE.TubeGeometry(curve, segments, radius, 6, false);
  const material = new THREE.MeshBasicMaterial({
    color, transparent: true, opacity: clamp(opacity, 0, 1),
    depthTest: true, depthWrite: false,
    blending: additive ? THREE.AdditiveBlending : THREE.NormalBlending,
    toneMapped: false,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.renderOrder = 3;
  group.add(mesh);
}

/**
 * A real X/Z arc strip. origin is its centre in world space; angles are radians.
 * progress advances the head from startAngle to endAngle and leaves a ~1.2rad tail.
 * power controls material width/detail, NOT reach or game damage. Supply the
 * proposed 25% larger reach through radius. tilt is an optional X-axis angle.
 * NEW shared texture: references/new-steel/ribbon.png (do not dispose it here).
 */
export function createBladeRibbon({
  origin = new THREE.Vector3(0, 1, 0), radius = 2.5,
  startAngle = -1.2, endAngle = 1.2, progress = 1,
  opacity = 1, power = 1, texture = null, tilt = 0,
} = {}) {
  const group = new THREE.Group();
  group.name = 'preview-3d-steel-ribbon';
  group.position.copy(origin);
  group.rotation.x = finite(tilt, 0);
  group.userData.sharedTexture = texture;
  group.userData.doNotDisposeSharedTexture = true;
  radius = Math.max(.05, finite(radius, 2.5));
  power = clamp(finite(power, 1), .35, 3);
  progress = clamp(finite(progress, 0), 0, 1);
  opacity = clamp(finite(opacity, 1), 0, 1);
  const total = endAngle - startAngle;
  if (opacity <= .001 || progress <= .001 || Math.abs(total) < .002) return group;
  const direction = Math.sign(total);
  const head = mix(startAngle, endAngle, progress);
  const travelled = Math.abs(total) * progress;
  const tailLength = Math.min(travelled, 1.2 + .12 * Math.min(power - 1, 1));
  const tail = head - direction * tailLength;
  const width = Math.min(radius * .29, radius * (.17 + .035 * power));
  const steps = Math.max(16, Math.ceil(tailLength * 42));
  const reveal = smooth(Math.min(1, travelled / .18));

  // A restrained dark spine behind the textured body gives depth and prevents
  // silhouette washout. It occupies only the inboard part of the same blade path.
  const spineMaterial = new THREE.MeshStandardMaterial({
    color: 0x27303e, metalness: .65, roughness: .37,
    transparent: true, opacity: opacity * reveal * .43,
    side: THREE.DoubleSide, depthTest: true, depthWrite: false,
  });
  const spine = new THREE.Mesh(
    bandGeometry(radius, tail, head, width * .32, -width * .24, -.004, steps),
    spineMaterial,
  );
  spine.renderOrder = 1;
  group.add(spine);

  const bladeMaterial = new THREE.MeshStandardMaterial({
    color: 0xd1d8e3, map: texture, metalness: .56, roughness: .3,
    emissive: 0x171c25, emissiveIntensity: .26,
    transparent: true, opacity: opacity * reveal * .92,
    alphaTest: .018, side: THREE.DoubleSide,
    depthTest: true, depthWrite: false,
  });
  const blade = new THREE.Mesh(bandGeometry(radius, tail, head, width, 0, 0, steps), bladeMaterial);
  blade.renderOrder = 2;
  group.add(blade);

  // Fine contrasting cutting edge. Its thickness is a small fraction of the
  // textured blade, never a second broad white crescent over the material.
  tube(group, bladeEdgeCurve(radius, tail, head, width, .18, .006),
    .009 * Math.sqrt(power), 0xe9c892, opacity * reveal * .55, steps, false);
  tube(group, bladeEdgeCurve(radius, tail, head, width, .61, .009),
    .005 * Math.sqrt(power), 0xf7f2df, opacity * reveal * .65, Math.max(12, Math.ceil(steps * .4)), true);
  return group;
}

function hash(seed, n) {
  const value = Math.sin((finite(seed, 1) + n * 19.187) * 12.9898) * 43758.5453;
  return value - Math.floor(value);
}

function jaggedPath(points, time, seed, amplitude = 1) {
  const output = [];
  for (let edge = 0; edge < points.length - 1; edge++) {
    const a = points[edge], b = points[edge + 1];
    const delta = new THREE.Vector3().subVectors(b, a);
    const length = delta.length();
    if (length < .0001) continue;
    const forward = delta.clone().normalize();
    const across = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0));
    if (across.lengthSq() < .001) across.set(1, 0, 0);
    across.normalize();
    const up = new THREE.Vector3().crossVectors(across, forward).normalize();
    const steps = clamp(Math.ceil(length / .26), 5, 24);
    for (let i = 0; i < steps; i++) {
      const u = i / steps, key = edge * 31 + i;
      const envelope = Math.sin(u * Math.PI);
      const p = new THREE.Vector3().lerpVectors(a, b, u);
      // Fixed seeded corners carry the shape. Only a small smoothly evolving
      // component moves with time, so the main trunk never hard-reseeds or jumps.
      const amount = Math.min(.19, length * .07) * envelope * amplitude;
      const phase = hash(seed, key + 1) * Math.PI * 2;
      const x = (hash(seed, key + 2) - .5) * 1.65 + Math.sin(time * 4.2 + phase) * .16;
      const y = (hash(seed, key + 3) - .5) * 1.2 + Math.sin(time * 3.4 + phase * 1.3) * .12;
      p.addScaledVector(across, x * amount).addScaledVector(up, y * amount);
      output.push(p);
    }
  }
  output.push(points[points.length - 1].clone());
  return output;
}

function polyCurve(points) {
  const curve = new THREE.CurvePath();
  for (let i = 0; i < points.length - 1; i++) {
    curve.add(new THREE.LineCurve3(points[i], points[i + 1]));
  }
  return curve;
}

/**
 * Connected 3D lightning along the supplied world-space polyline. Caller chooses
 * real target topology; decorative branches do not recruit/damage extra targets.
 * The stable main core evolves smoothly; only the few secondary branches breathe.
 */
export function createLightning({ points = [], time = 0, opacity = 1, power = 1, seed = 1 } = {}) {
  const group = new THREE.Group();
  group.name = 'preview-3d-connected-lightning';
  points = points.filter(p => p && Number.isFinite(p.x) && Number.isFinite(p.y) && Number.isFinite(p.z));
  if (points.length < 2) return group;
  time = finite(time, 0);
  opacity = clamp(finite(opacity, 1), 0, 1);
  power = clamp(finite(power, 1), .35, 3);
  if (opacity <= .001) return group;
  const pathPoints = jaggedPath(points, time, seed, 1);
  if (pathPoints.length < 2) return group;
  const curve = polyCurve(pathPoints);
  const length = curve.getLength();
  if (length < .01) return group;
  const segments = clamp(Math.ceil(length * 16), 24, 160);
  const radius = .032 + .022 * Math.sqrt(power);
  // No white strobe: the stable core varies by only 3% at a slow continuous rate.
  const stable = .97 + Math.sin(time * 6 + hash(seed, 74) * 6.28) * .03;
  tube(group, curve, radius * 2.35, 0x5167cb, opacity * .22, segments, true);
  tube(group, curve, radius, 0x879aff, opacity * .75 * stable, segments, true);
  tube(group, curve, radius * .43, 0xe9f1ff, opacity * .91 * stable, segments, false);

  const count = clamp(Math.floor(power + .6), 1, 3);
  for (let i = 0; i < count; i++) {
    const fraction = .28 + i * .21 + (hash(seed, 90 + i) - .5) * .055;
    const start = curve.getPointAt(clamp(fraction, .1, .87));
    const tangent = curve.getTangentAt(clamp(fraction, .1, .87)).normalize();
    let side = new THREE.Vector3().crossVectors(tangent, new THREE.Vector3(0, 1, 0));
    if (side.lengthSq() < .001) side.set(1, 0, 0);
    side.normalize().multiplyScalar(i % 2 ? -1 : 1);
    const branchLength = Math.min(length * .25, .48 + hash(seed, 114 + i) * .75) * Math.sqrt(power);
    const end = start.clone()
      .addScaledVector(side, branchLength)
      .addScaledVector(tangent, branchLength * .35);
    end.y += (hash(seed, 125 + i) - .5) * branchLength * .8;
    const mid = start.clone().lerp(end, .55);
    mid.y += Math.sin(time * 4.6 + hash(seed, 135 + i) * 6.28) * .045;
    const branch = polyCurve(jaggedPath([start, mid, end], time, seed + i * 13.7 + 40, .65));
    const breathing = .8 + Math.sin(time * 5.2 + hash(seed, 150 + i) * 6.28) * .1;
    tube(group, branch, radius * .52, 0x9aaaff, opacity * .53 * breathing, 24, true);
    tube(group, branch, radius * .21, 0xe3edff, opacity * .66 * breathing, 24, false);
  }
  group.userData.decorativeBranchesOnly = true;
  group.userData.geometryIsWorldSpace = true;
  return group;
}
