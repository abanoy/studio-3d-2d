shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;
varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 coordinates = world_position.xz;
	vec2 derivatives = max(fwidth(coordinates), vec2(0.0001));
	vec2 cell = abs(fract(coordinates - 0.5) - 0.5) / derivatives;
	float line = 1.0 - min(min(cell.x, cell.y), 1.0);
	float fade = 1.0 - smoothstep(8.0, 80.0, distance(world_position, CAMERA_POSITION_WORLD));
	// Fade subpixel cells before they form distracting patterns at the horizon.
	float readable = 1.0 - smoothstep(0.35, 1.0, max(derivatives.x, derivatives.y));
	ALBEDO = vec3(1.0);
	ALPHA = line * fade * readable * 0.65;
}
