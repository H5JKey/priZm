#version 430 core

layout(rgba32f, binding = 0) uniform writeonly image2D normalMap;
layout(rgba32f, binding = 1) uniform writeonly image2D albedoMap;

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

layout(std430, binding = 2) buffer vertexBuffer {
    vec4 vertices[];
};

layout(std430, binding = 3) buffer texCoordBuffer {
    vec4 texCoords[];
};

layout(std430, binding = 4) buffer vertexIndexBuffer {
    int verticesIndices[];
};

layout(std430, binding = 5) buffer materialBuffer {
    Material materials[];
};

layout(std430, binding = 6) buffer materialIndexBuffer {
    int materialsIndices[];
};

layout(std430, binding = 7) buffer bvhNodesBuffer {
    Node bvhNodes[];
};

layout(std430, binding = 8) buffer bvhTrianglesBuffer {
    int bvhTriangles[];
};

layout(binding = 9) uniform sampler2DArray textureArray;


uniform vec3 uOrigin;
uniform float uFov;
uniform vec3 uLookAt;

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

vec3 getAlbedo(Material material, vec2 texCoord) {
    if (material.albedoTextureID == -1) {
        return material.albedo.rgb;
    } else {
        return texture(textureArray, vec3(texCoord, float(material.albedoTextureID))).rgb;
    }
}

void main() {
    ivec2 pixel = ivec2(gl_GlobalInvocationID.xy);
    ivec2 size =  imageSize(normalMap);

    if (pixel.x >= size.x || pixel.y >= size.y) {
        return;
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

    vec2 uv = (2.0*vec2(pixel) - vec2(size)) / vec2(size).y;
    uv.y = -uv.y;

    vec3 direction = normalize(forward + right * uFov * uv.x + up * uFov * uv.y);

    HitInfo hit;
    if (bvhNodes.length() > 0) {
        hit = castRayThroughBVH(uOrigin, direction);
    }
    else {
        imageStore(normalMap, pixel, vec4(0.0,0.0,0.0, 1.0));
        imageStore(albedoMap, pixel, vec4(0.0,0.0,0.0, 1.0));
        return;
    }

    if (hit.distance > MAX_DIST - 1) {
        imageStore(normalMap, pixel, vec4(0,0,0, 1.0));
        imageStore(albedoMap, pixel, vec4(0,0,0, 1.0));
    }
    else {
        imageStore(normalMap, pixel, vec4(hit.normal , 1.0));
        imageStore(albedoMap, pixel, vec4(getAlbedo(materials[hit.material_id],hit.texCoord) , 1.0));
    }
    
}
