#version 330 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;
layout(location = 2) in vec2 uv;

out vec3 fragNormal;
out float fragHeight;
out vec3 fragWorldPos;
out vec2 fragUV;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

void main()
{
    vec4 worldPos = model * vec4(position, 1.0);
    fragWorldPos = worldPos.xyz;
    fragHeight = position.y;
    fragUV = uv;

    mat3 normalMatrix = transpose(inverse(mat3(model)));
    fragNormal = normalize(normalMatrix * normal);

    gl_Position = projection * view * worldPos;
}
