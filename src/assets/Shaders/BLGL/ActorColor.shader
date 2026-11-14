shader_type spatial;
render_mode cull_disabled;
uniform vec4 base_color = vec4(0.25,0.18,0.1,1.0);
uniform float roughness = 0.75;
uniform float metallic = 0.0;
void fragment() {
    ALBEDO = base_color.rgb;
    ROUGHNESS = roughness;
    METALLIC = metallic;
}
