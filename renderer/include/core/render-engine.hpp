#pragma once
#include <glad/gl.h>

#include <random>

#include "bvh-builder.hpp"
#include "bvh.hpp"
#include "denoiser.hpp"
#include "glm/ext/vector_float4.hpp"
#include "logger.hpp"
#include "render-target.hpp"
#include "scene.hpp"


class RenderEngine {
    struct GPUMaterial {
        glm::vec4 albedo;
        glm::vec4 emission;
        glm::vec4 attenuationColor;
        float thicknessFactor;
        float attenuationDistance;
        float metalness;
        float roughness;
        float transmission;
        float ior;
        int albedoTextureID;

       private:
        float padding;
    };

    struct GPUData {
        std::vector<glm::vec4> vertices;
        std::vector<int> vertexIndices;
        std::vector<GPUMaterial> materials;
        std::vector<int> materialIndices;
        std::vector<glm::vec4> texCoords;
    };

    Denoiser denoiser;
    MedianBuilder bvhBuilder;
    Logger logger;
    GLuint pathTracingProgram = 0;
    GLuint postProcessingProgram = 0;
    GLuint gbufferProgram = 0;

    GLuint vertexSSBO = 0;
    GLuint vertexIndexSSBO = 0;
    GLuint materialSSBO = 0;
    GLuint materialIndexSSBO = 0;
    GLuint bvhNodesSSBO = 0;
    GLuint bvhTrianglesSSBO = 0;
    GLuint texCoordSSBO = 0;
    GLuint textureArray = 0;

    std::random_device rd;
    std::mt19937 gen;
    std::uniform_int_distribution<uint> uniformDistr;

   public:
    RenderEngine();
    void renderFrame(RenderTarget& target, const Scene& scene, int samples);
    void destroy();
    ~RenderEngine();

   private:
    void pathTracing(RenderTarget& target, const Scene::Camera& camera, const glm::vec3 backgroundColor, int samples);
    void fillGbuffer(RenderTarget& target, const GPUData& gpuData, const Scene::Camera& camera);
    void postProcess(RenderTarget& target) const;
    void uploadGPUBuffers(const GPUData& gpuData, const BVH& bvh);
    GLuint compileShader(const std::string& source);
    void loadTextures(const std::vector<Scene::TextureData>& textures);
    GPUData convertSceneToGPUData(const Scene& scene);
    void resetState();
};