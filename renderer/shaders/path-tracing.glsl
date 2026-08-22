#version 430 core

struct Material {
    vec4 albedo;
    vec4 emission;
    vec4 attenuationColor;
    float thicknessFactor;
    float attenuationDistance;
    float metalness;
    float roughness;
    float transmission;
    float ior;
    int albedoTextureID;
};

struct Node {
    vec4 min, max;
    int left, right;
    int start;
    int count;
};

struct Sun {
    vec3 direction;
    vec3 color;
    float exponent;
};

layout(rgba32f, binding = 0) uniform image2D outputImage;

layout(std430, binding = 1) buffer vertexBuffer {
    vec4 vertices[];
};

layout(std430, binding = 2) buffer texCoordBuffer {
    vec4 texCoords[];
};

layout(std430, binding = 3) buffer vertexIndexBuffer {
    int verticesIndices[];
};

layout(std430, binding = 4) buffer materialBuffer {
    Material materials[];
};

layout(std430, binding = 5) buffer materialIndexBuffer {
    int materialsIndices[];
};

layout(std430, binding = 6) buffer bvhNodesBuffer {
    Node bvhNodes[];
};

layout(std430, binding = 7) buffer bvhTrianglesBuffer {
    int bvhTriangles[];
};

layout(binding = 8) uniform sampler2DArray textureArray;

uniform vec3 uOrigin;
uniform float uFov;
uniform vec3 uLookAt;
uniform vec3 uBackgroundColor;
uniform uint uSeed;
uniform uint uFrameIndex;
uniform Sun uSun;

layout(local_size_x = 16, local_size_y = 16) in;


struct HitInfo {
    float distance;
    vec3 position;
    int material_id;
    vec3 normal;
    vec2 texCoord; 
};

HitInfo triangleIntersection(vec3 ro, vec3 rd, int triangle_idx) {
    HitInfo info;
    
    vec3 v0 = vertices[verticesIndices[3*triangle_idx]].xyz;
    vec3 v1 = vertices[verticesIndices[3*triangle_idx+1]].xyz;
    vec3 v2 = vertices[verticesIndices[3*triangle_idx+2]].xyz;

    vec3 e1 = v1 - v0;
    vec3 e2 = v2 - v0;

    vec3 pvec = cross(rd, e2);
    float det = dot(e1, pvec);

    if (abs(det) < 1e-8) {
        info.distance = -1.0;
        info.position = vec3(0.0);
        info.normal = vec3(0.0);
        info.material_id = 0;
        return info;
    }

    float inv_det = 1.0 / det;
    vec3 tvec = ro - v0;

    float u = dot(tvec, pvec) * inv_det;
    if (u < 0.0 || u > 1.0) {
        info.distance = -1.0;
        info.position = vec3(0.0);
        info.normal = vec3(0.0);
        info.material_id = 0;
        return info;
    }

    vec3 qvec = cross(tvec, e1);

    float v = dot(rd, qvec) * inv_det;
    if (v < 0.0 || u + v > 1.0) {
        info.distance = -1.0;
        info.position = vec3(0.0);
        info.normal = vec3(0.0);
        info.material_id = 0;
        return info;
    }

    float t = dot(e2, qvec) * inv_det;
    if (t < 1e-8) {
        info.distance = -1.0;
        info.position = vec3(0.0);
        info.normal = vec3(0.0);
        info.material_id = 0;
        return info;
    }
    vec2 uv0 = texCoords[verticesIndices[3*triangle_idx]].xy;
    vec2 uv1 = texCoords[verticesIndices[3*triangle_idx+1]].xy;
    vec2 uv2 = texCoords[verticesIndices[3*triangle_idx+2]].xy;

    info.texCoord = (1.0 - u - v) * uv0 + u * uv1 + v * uv2;
    info.distance = t;
    info.position = ro + rd * t;
    info.normal = normalize(cross(v1 - v0, v2 - v0));
    info.material_id = materialsIndices[triangle_idx];
    return info;
}

const float EPSILON = 1e-6f;
float AABBIntersection(vec3 origin, vec3 direction, vec3 boxMin, vec3 boxMax) {
    vec3 invDir = 1.0f / direction;

    vec3 t0 = (boxMin - origin) * invDir;
    vec3 t1 = (boxMax - origin) * invDir;

    vec3 tNear = vec3(
        min(t0.x, t1.x),
        min(t0.y, t1.y),
        min(t0.z, t1.z)
    );
    vec3 tFar = vec3(
        max(t0.x, t1.x),
        max(t0.y, t1.y),
        max(t0.z, t1.z)
    );

    float tMin = max(max(tNear.x, tNear.y), max(tNear.z, 0.0f));
    float tMax = min(min(tFar.x, tFar.y), tFar.z);
    if (tMax >= 0.0 && tMin <= tMax + EPSILON)
        return tMin;
    else
        return -1.0;
}


uint pcg(uint seed) {
    uint state = seed * uint(747796405) + uint(2891336453u);
	uint word = ((state >> ((state >> uint(28)) + uint(4))) ^ state) * uint(277803737);
	return (word >> uint(22)) ^ word;
}

float random(uint seed) {
    return pcg(seed) / float(uint(0xffffffff));
}

vec2 random2(uint seed) {
    return vec2(random(seed), random(seed+1));
}

vec3 cosineHemisphere(uint seed, vec3 N) {
    float u1 = random(seed);
    float u2 = random(seed + 1);
    float r = sqrt(u1);
    float theta = 2.0 * 3.14159265 * u2;
    float x = r * cos(theta);
    float y = sqrt(1.0 - u1);
    vec3 local = vec3(x, y, r * sin(theta));

    vec3 T;
    if (abs(N.z) < 0.999)
        T = normalize(cross(vec3(0,0,1), N));
    else
        T = normalize(cross(vec3(1,0,0), N));

    vec3 B = cross(N, T);
    return normalize(
        local.x * T +
        local.y * N +
        local.z * B
    );
}

const float MAX_DIST=100000.0;
HitInfo castRayTroughAABB(vec3 origin, vec3 direction, Node node) {
    HitInfo closestHitInfo;
    closestHitInfo.distance = MAX_DIST;
    closestHitInfo.position = vec3(0);
    closestHitInfo.normal = vec3(0);
    closestHitInfo.material_id = -1;
    
    for (int i=node.start; i<node.count+node.start; i++) {
        HitInfo info = triangleIntersection(origin, direction, bvhTriangles[i]);
        if (info.distance > 0.0 && info.distance < closestHitInfo.distance) {
            closestHitInfo = info;
        }
    }
    return closestHitInfo;
}

HitInfo castRayThroughBVH(vec3 origin, vec3 direction) {
    HitInfo closestHitInfo;
    closestHitInfo.distance = MAX_DIST;
    closestHitInfo.position = vec3(0);
    closestHitInfo.normal = vec3(0);
    closestHitInfo.material_id = -1;

    int stack[1024];
    int stackPtr = 0;

    stack[stackPtr++] = 0;
    while (stackPtr > 0) {
        int nodeIdx = stack[--stackPtr];
        Node node = bvhNodes[nodeIdx];
        float t = AABBIntersection(origin, direction, node.min.xyz, node.max.xyz);
        if (t < 0.0 || t > closestHitInfo.distance + EPSILON)
            continue;
        if (node.left == -1 && node.right == -1) {
            HitInfo info = castRayTroughAABB(origin, direction, node);
            if (info.distance > 0 && info.distance < closestHitInfo.distance)
                closestHitInfo = info;
        }
        else {
            if (node.left != -1) 
                stack[stackPtr++] = node.left;
            if (node.right != -1)
                stack[stackPtr++] = node.right;
        }
    }
    return closestHitInfo;
}

vec3 schlickFresnel(vec3 V, vec3 H, vec3 R0) {
    float cosTheta = clamp(dot(H, V),0.0,1.0);
    return R0 + (vec3(1.0) - R0) * pow((1 - cosTheta), 5.0);
}

vec3 GGX(uint seed, vec3 N, float roughness) {
    float u1 = random(seed);
    float u2 = random(seed + 1);
    float theta = atan(roughness * roughness * sqrt(u1) / sqrt(1 - u1));
    float phi = 2 * 3.141592 * u2;

    float sinTheta = sin(theta);
    vec3 local = vec3(sinTheta * cos(phi), cos(theta), sinTheta * sin(phi));
    vec3 T;
    if (abs(N.z) < 0.999) {
        T = normalize(cross(vec3(0,0,1), N));
    }
    else {
        T = normalize(cross(vec3(1,0,0), N));
    }
    vec3 B = normalize(cross(N, T));

    return normalize(local.x * T + local.y * N + local.z * B);
}

float distribution(vec3 H, vec3 N, float roughness) {
    float a = roughness * roughness;
    float a2 = a*a;
    return a2 / (3.141592 * pow((pow(dot(N,H), 2.0) * (a2 - 1.0) + 1.0), 2.0));
}

float schlickGGX(vec3 N, vec3 V, float roughness) {
    float k = pow((roughness + 1.0), 2.0) / 8.0;
    return dot(N,V) / (dot(N,V) * (1.0 - k) + k);
}

float smith(vec3 N, vec3 V, vec3 L, float roughness) {
    return schlickGGX(N, V, roughness) * schlickGGX(N, L, roughness);
}

vec3 getAlbedo(Material material, vec2 texCoord) {
    if (material.albedoTextureID == -1) 
        return material.albedo.rgb;
    else
        return texture(textureArray, vec3(texCoord, float(material.albedoTextureID))).rgb;
}

vec3 traceRay(vec3 origin, vec3 direction, uint seed) {
    float pathDistance = 0;
    bool insideTransparent = false;
    vec3 throughput = vec3(1.0);
    const int bounces = 8;
    for (int i=0; i<bounces; i++) {
        if (i > 4) {
            float p = max(max(throughput.r, throughput.g), throughput.b);
            p = clamp(p,0.05, 0.95);
            if (random(seed) > p) break;
            seed = pcg(seed);
            throughput /= p;
        }
        seed = pcg(seed);
        HitInfo hit;
        if (bvhNodes.length() > 0)
            hit = castRayThroughBVH(origin, direction);
        else
            hit.distance = MAX_DIST;
        if (hit.distance > MAX_DIST - 1) {
            return throughput * (uBackgroundColor + uSun.color * pow(max(0.0, dot(direction, uSun.direction)), uSun.exponent));
        }
        Material material = materials[hit.material_id];
        if (length(material.emission.rgb) > 0.01) {
            return throughput * material.emission.rgb;
        }
        vec3 H,L;
        vec3 N = hit.normal;
        if (dot(N, direction) > 0.0) N = -N;
        vec3 V = normalize(-direction);
        do {
            H = GGX(seed, N, material.roughness);
            L = reflect(-V, H);
            seed = pcg(seed);
        } while (dot(L, N) <= 0.0);
        vec3 F0 = mix(vec3(pow((material.ior - 1) / (material.ior + 1), 2.0)), getAlbedo(material, hit.texCoord), material.metalness);
        vec3 F = schlickFresnel(V, H, F0);
        if (material.metalness > 0.0) {
            if (material.roughness < 0.01) {
                throughput *= schlickFresnel(-direction, hit.normal, F0);
                if (!insideTransparent)
                    pathDistance = 0.0;
                pathDistance+=distance(hit.position, origin);
                origin = hit.position + hit.normal * 0.001;
                direction = reflect(direction, hit.normal);
                continue;
            }
            float G = smith(N, V, L, material.roughness);
            float D = distribution(H, N, material.roughness);
            vec3 fr = (D * F * G) / (4 * dot(N,V) * dot(N, L));
            float pdf = D * dot(N,H) / (4 * dot(V,H));
            throughput *= fr * dot (N, L) / pdf;
            if (!insideTransparent)
                pathDistance = 0.0;
            pathDistance+=distance(hit.position, origin);
            origin = hit.position + N * 0.001;
            direction = L;
            continue;
        }
        else {
            seed = pcg(seed+2);
            float r = random(seed);
            if (r < F.x) {
                if (material.roughness < 0.01) {
                    if (!insideTransparent)
                        pathDistance = 0.0;
                    pathDistance+=distance(hit.position, origin);
                    origin = hit.position + N * 0.001;
                    direction = reflect(direction, N);
                    throughput *= getAlbedo(material, hit.texCoord) / F.x;
                    continue;
                }
                float G = smith(N, V, L, material.roughness);
                float D = distribution(H, N, material.roughness);
                vec3 fr = (D * F * G) / (4 * dot(N,V) * dot(N, L));
                float pdf = D * dot(N,H) / (4 * dot(V,H));
                throughput *= fr * dot (N, L) / (pdf * F.x);
                if (!insideTransparent)
                    pathDistance = 0.0;
                pathDistance+=distance(hit.position, origin);
                origin = hit.position + hit.normal * 0.001;
                direction = L;
            }
            else {
                seed = pcg(seed);
                if (material.transmission > 0.0) {
                    bool frontFace = dot(direction, hit.normal) < 0.0;
                    vec3 N = frontFace ? hit.normal : - hit.normal;
                    float eta = frontFace ? (1.0 / material.ior) : material.ior;
                    
                    vec3 T = refract(direction, N, eta);
                    if (length(T) == 0.0) {
                        direction = reflect(direction, N);
                        origin = hit.position + N * 0.001;
                       if (!insideTransparent)
                            pathDistance = 0.0;
                        pathDistance+=distance(hit.position, origin);
                    }
                    else {
                        pathDistance = distance(origin, hit.position);
                        direction = T;
                        origin = hit.position - N * 0.001;
                        if (!frontFace) {
                            vec3 sigma = -log(material.attenuationColor.rgb) / material.attenuationDistance;
                            throughput *= exp(-sigma * pathDistance) / (1 - F.x);
                            insideTransparent = false;
                            pathDistance = 0.0;
                        }
                        else {
                            insideTransparent = true;
                            pathDistance = 0.0;
                        }
                    }
                }
                else {
                    vec3 N = hit.normal;
                    if (dot(direction, N) > 0.0) {
                        N = -N;
                    }
                    direction = cosineHemisphere(seed, N);
                    if (!insideTransparent)
                        pathDistance = 0.0;
                    pathDistance+=distance(hit.position, origin);
                    origin = hit.position + N * 0.001;
                    throughput *= getAlbedo(material, hit.texCoord) / (1 - F.x);
                }
            }
        }
    }
    return vec3(0.0);
}


void main() {
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
    ivec2 size =  imageSize(outputImage);

    if (pixel.x >= size.x || pixel.y >= size.y) {
        return;
    }
    vec3 oldColor;
    if (uFrameIndex == 0) {
        oldColor = vec3(0);
    } else {
        oldColor = imageLoad(outputImage, pixel).rgb;
    }

    vec3 forward = normalize(uLookAt - uOrigin);
    vec3 right;
    vec3 up;
    if (abs(dot(forward, vec3(0.0, 1.0, 0.0))) > 0.999) {
        right = vec3(1.0, 0.0, 0.0);
        up = cross(forward, right);
    } else {
        right = normalize(cross(vec3(0.0, 1.0, 0.0), forward));
        up = normalize(cross(forward, right));
    }

    uint seed = uSeed + 6732 * uint(pixel.x) + 8157 * uint(pixel.y);
    vec2 jitter = random2(seed) - vec2(0.5, 0.5);
    vec2 uv = (2.0*vec2(pixel) + jitter - vec2(size)) / vec2(size).y;
    uv.y = -uv.y;
    
    vec3 direction = normalize(forward + right * uFov * uv.x + up * uFov * uv.y);

    vec3 color = traceRay(uOrigin, direction, seed);

    color = mix(oldColor, color, 1.0 / (uFrameIndex + 1));
    imageStore(outputImage, pixel, vec4(color, 1.0));
}
