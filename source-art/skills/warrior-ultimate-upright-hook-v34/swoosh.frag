vec4 frag () {
  float u = v_uv.x;
  float v = v_uv.y;
  float clock = flowState.x;
  vec3 n = texture(flowTexture, vec2(u * 1.9 - clock * 0.17, v * 1.4 - clock * 0.36)).rgb;
  vec3 m = texture(flowTexture, vec2(u * 3.6 + clock * 0.08, v * 2.3 - clock * 0.63)).rgb;
  float flow = n.r * 0.64 + m.g * 0.36;
  float head = smoothstep(0.32, 0.76, u);
  float warp = (flow - 0.5) * (0.045 + v * 0.055);
  float depth = v + warp;
  float crest = exp(-pow((depth - 0.27) / (0.18 + head * 0.08), 2.0));
  float air = exp(-pow((depth - 0.56) / 0.32, 2.0));
  float fibers = smoothstep(0.29, 0.70, n.b * 0.60 + m.r * 0.40);
  float cap = smoothstep(0.0, 0.014, u) * (1.0 - smoothstep(0.973, 1.0, u));
  float edge = smoothstep(0.0, 0.055, v) * (1.0 - smoothstep(0.77, 1.0, v));
  float end = clamp(flowState.y, 0.0, 1.0);
  float frontLife = 1.0 - smoothstep(0.23, 0.88, end);
  float wakeLife = 1.0 - smoothstep(0.52, 1.0, end);
  float erosion = smoothstep(end * 1.10 - 0.13, end * 1.10 + 0.13, flow + v * 0.19);
  float density = crest * (0.64 + head * 0.23 + n.g * 0.13) * frontLife
    + air * (0.08 + fibers * 0.22) * wakeLife;
  float axial = 0.30 + 0.70 * smoothstep(0.36, 0.76, u);
  float alpha = min(0.88, density * axial * cap * edge * erosion * mainColor.a);
  if (alpha < 0.002) discard;
  vec3 silver = mainColor.rgb * (0.93 + fibers * 0.07);
  return CCFragOutput(vec4(SRGBToLinear(silver), alpha));
}
