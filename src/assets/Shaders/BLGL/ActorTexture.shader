shader_type spatial;
render_mode cull_disabled;
uniform sampler2D albedo_map : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 base_color = vec4(1.0);
uniform float roughness = 0.75;
uniform float metallic = 0.0;
uniform float alpha_cut = 0.001;
void fragment() {
    vec4 tex = texture(albedo_map, UV);
    ALBEDO = tex.rgb * base_color.rgb;
    ALPHA = tex.a;
    ALPHA_SCISSOR_THRESHOLD = alpha_cut;
    ROUGHNESS = roughness;
    METALLIC = metallic;
}
