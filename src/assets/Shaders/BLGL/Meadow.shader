shader_type spatial;
render_mode cull_disabled;
void vertex() {
    VERTEX.x += sin(TIME*1.8+VERTEX.x*2.0+VERTEX.z*1.7)*UV.y*0.07;
}
void fragment() {
    ALBEDO=mix(vec3(0.10,0.20,0.055),vec3(0.38,0.48,0.15),UV.y);
    ROUGHNESS=0.96;
}
