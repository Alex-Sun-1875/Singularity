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
  float crest = exp(-pow((depth - 0.15) / (0.075 + head * 0.025), 2.0));
  float mantle = exp(-pow((depth - 0.30) / (0.18 + head * 0.04), 2.0));
  float echo = exp(-pow((depth - 0.43 - n.g * 0.04) / 0.033, 2.0));
  float air = exp(-pow((depth - 0.56) / 0.32, 2.0));
  float fibers = smoothstep(0.29, 0.70, n.b * 0.60 + m.r * 0.40);
  float cap = smoothstep(0.0, 0.014, u) * (1.0 - smoothstep(0.973, 1.0, u));
  float edge = smoothstep(0.0, 0.055, v) * (1.0 - smoothstep(0.77, 1.0, v));
  float end = clamp(flowState.y, 0.0, 1.0);
  float frontLife = 1.0 - smoothstep(0.23, 0.88, end);
  float wakeLife = 1.0 - smoothstep(0.52, 1.0, end);
  float erosion = smoothstep(end * 1.12 - 0.18, end * 1.12 + 0.20, flow + v * 0.19);
  float density = (crest * (0.94 + head * 0.12) + mantle * (0.33 + fibers * 0.17)
    + echo * fibers * 0.08) * frontLife + air * (0.035 + fibers * 0.12) * wakeLife;
  float axial = 0.30 + 0.70 * smoothstep(0.36, 0.76, u);
  float alpha = min(0.88, density * axial * cap * edge * erosion * mainColor.a);
  if (alpha < 0.002) discard;
  vec3 silver = mix(mainColor.rgb * 0.78, vec3(0.92, 0.96, 0.98), crest * 0.82);
  return CCFragOutput(vec4(SRGBToLinear(silver), alpha));
}
