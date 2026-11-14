shader_type spatial;
uniform vec3 base_color = vec3(0.22, 0.30, 0.12);
uniform float grain_scale = 4.0;
uniform float roughness = 0.94;
float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
float noise(vec2 p) {
    vec2 i=floor(p); vec2 f=fract(p); f=f*f*(3.0-2.0*f);
    return mix(mix(hash(i),hash(i+vec2(1.0,0.0)),f.x),mix(hash(i+vec2(0.0,1.0)),hash(i+vec2(1.0,1.0)),f.x),f.y);
}
void fragment() {
    vec2 p=VERTEX.xz*grain_scale;
    float grain=noise(p)*0.42+noise(p*3.1)*0.26+noise(p*11.0)*0.13;
    ALBEDO=base_color*(0.68+grain*0.63);
    ROUGHNESS=roughness;
    METALLIC=0.0;
}
