#version 330 core

in vec3 fragNormal;
in float fragHeight;
in vec3 fragWorldPos;
in vec2 fragUV;

out vec4 FragColor;

uniform vec3      lightDir;
uniform float     minHeight;
uniform float     maxHeight;
uniform sampler2D satelliteTexture;
uniform bool      hasSatellite;

void main()
{
    vec3 normal = normalize(fragNormal);

    // ── BASE COLOR ───────────────────────────────────────────────────────────
    vec3 baseColor;

    if (hasSatellite) {
        baseColor = texture(satelliteTexture, fragUV).rgb;
    } else {
        float heightNorm = (fragHeight - minHeight) /
                           max(maxHeight - minHeight, 0.001);

        vec3 grassColor = vec3(0.25, 0.50, 0.22);
        vec3 dirtColor  = vec3(0.48, 0.38, 0.26);
        vec3 rockColor  = vec3(0.52, 0.49, 0.44);
        vec3 snowColor  = vec3(0.95, 0.95, 0.98);

        if (heightNorm < 0.3)
            baseColor = mix(grassColor, dirtColor, heightNorm / 0.3);
        else if (heightNorm < 0.6)
            baseColor = mix(dirtColor, rockColor, (heightNorm-0.3)/0.3);
        else if (heightNorm < 0.85)
            baseColor = mix(rockColor, snowColor, (heightNorm-0.6)/0.25);
        else
            baseColor = snowColor;
    }

    // ── SKIRT WALLS → dark rock color ───────────────────────────────────────
    if (abs(normal.y) < 0.1) {
        baseColor = vec3(0.18, 0.13, 0.09);
    }

    // ── HILLSHADING ──────────────────────────────────────────────────────────
    vec3 L       = normalize(lightDir);
    float diffuse = max(dot(normal, L), 0.0);

    // Ambient occlusion from slope
    float slope = 1.0 - abs(dot(normal, vec3(0.0, 1.0, 0.0)));
    float ao    = 1.0 - slope * 0.35;

    // Specular — subtle, only on flat surfaces
    vec3  viewDir = normalize(-fragWorldPos);
    vec3  halfDir = normalize(L + viewDir);
    float specular = pow(max(dot(normal, halfDir), 0.0), 48.0)
                     * (1.0 - slope) * 0.12;

    // Combined lighting
    float lighting = (0.30 + diffuse * 0.70) * ao + specular;

    vec3 litColor = baseColor * lighting;

    // ── ATMOSPHERIC FOG ──────────────────────────────────────────────────────
    float dist      = length(fragWorldPos);
    float fogFactor = clamp(exp(-dist * 0.0006), 0.0, 1.0);
    vec3 fogColor   = vec3(0.45, 0.52, 0.65);

    vec3 finalColor = mix(fogColor, litColor, fogFactor);

    FragColor = vec4(finalColor, 1.0);
}
