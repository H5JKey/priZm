#include "render-engine.hpp"

#include <exception>
#include <string>

#include "context-guard.hpp"
#include "logger.hpp"
#include "render-target.hpp"
#include "utils.hpp"

void RenderEngine::destroy() {
    if (vertexSSBO) {
        glDeleteBuffers(1, &vertexSSBO);
        vertexSSBO = 0;
    }
    if (vertexIndexSSBO) {
        glDeleteBuffers(1, &vertexIndexSSBO);
        vertexIndexSSBO = 0;
    }
    if (materialSSBO) {
        glDeleteBuffers(1, &materialSSBO);
        materialSSBO = 0;
    }
    if (materialIndexSSBO) {
        glDeleteBuffers(1, &materialIndexSSBO);
        materialIndexSSBO = 0;
    }
    if (bvhNodesSSBO) {
        glDeleteBuffers(1, &bvhNodesSSBO);
        bvhNodesSSBO = 0;
    }
    if (bvhTrianglesSSBO) {
        glDeleteBuffers(1, &bvhTrianglesSSBO);
        bvhTrianglesSSBO = 0;
    }
    if (texCoordSSBO) {
        glDeleteBuffers(1, &texCoordSSBO);
        texCoordSSBO = 0;
    }
    if (textureArray) {
        glDeleteTextures(1, &textureArray);
        textureArray = 0;
    }
    if (pathTracingProgram) {
        glDeleteProgram(pathTracingProgram);
        pathTracingProgram = 0;
    }
    if (postProcessingProgram) {
        glDeleteProgram(postProcessingProgram);
        postProcessingProgram = 0;
    }
    if (gbufferProgram) {
        glDeleteProgram(gbufferProgram);
        gbufferProgram = 0;
    }
}

RenderEngine::RenderEngine() : gen(rd()), uniformDistr(0, 0xFFFFFFFF), bvhBuilder(-1, 4), logger("RENDERER") {
    try {
        logger.debug("Compiling path tracing shader");
        pathTracingProgram = compileShader(utils::readFromFile("shaders/path-tracing.glsl"));

        logger.debug("Compiling post processing shader");
        postProcessingProgram = compileShader(utils::readFromFile("shaders/post-processing.glsl"));

        logger.debug("Compiling gbuffer shader");
        gbufferProgram = compileShader(utils::readFromFile("shaders/gbuffer.glsl"));

    } catch (const std::exception& e) {
        logger.fatal(e.what());
        destroy();
        throw;
    }

    GLuint error;
    glGenBuffers(1, &vertexSSBO);
    error = glGetError();
    if (error != 0) {
        destroy();
        logger.fatal("Failed to create vertexSSBO. Error: " + std::to_string(error));
        throw std::runtime_error("Failed to create vertexSSBO. Error: " + std::to_string(error));
    }

    glGenBuffers(1, &texCoordSSBO);
    error = glGetError();
    if (error != 0) {
        destroy();
        logger.fatal("Failed to create texCoordSSBO. Error: " + std::to_string(error));
        throw std::runtime_error("Failed to create texCoordSSBO. Error: " + std::to_string(error));
    }

    glGenBuffers(1, &vertexIndexSSBO);
    error = glGetError();
    if (error != 0) {
        destroy();
        logger.fatal("Failed to create vertexIndexSSBO. Error: " + std::to_string(error));
        throw std::runtime_error("Failed to create vertexIndexSSBO. Error: " + std::to_string(error));
    }

    glGenBuffers(1, &materialSSBO);
    error = glGetError();
    if (error != 0) {
        destroy();
        logger.fatal("Failed to create materialSSBO. Error: " + std::to_string(error));
        throw std::runtime_error("Failed to create materialSSBO. Error: " + std::to_string(error));
    }

    glGenBuffers(1, &materialIndexSSBO);
    error = glGetError();
    if (error != 0) {
        destroy();
        logger.fatal("Failed to create materialIndexSSBO. Error: " + std::to_string(error));
        throw std::runtime_error("Failed to create materialIndexSSBO. Error: " + std::to_string(error));
    }

    glGenBuffers(1, &bvhNodesSSBO);
    error = glGetError();
    if (error != 0) {
        destroy();
        logger.fatal("Failed to create bvhNodesSSBO. Error: " + std::to_string(error));
        throw std::runtime_error("Failed to create bvhNodesSSBO. Error: " + std::to_string(error));
    }

    glGenBuffers(1, &bvhTrianglesSSBO);
    error = glGetError();
    if (error != 0) {
        destroy();
        logger.fatal("Failed to create bvhTrianglesSSBO. Error: " + std::to_string(error));
        throw std::runtime_error("Failed to create bvhTrianglesSSBO. Error: " + std::to_string(error));
    }
}

GLuint RenderEngine::compileShader(const std::string& source) {
    GLuint shader = glCreateShader(GL_COMPUTE_SHADER);
    const char* src = source.c_str();
    glShaderSource(shader, 1, &src, nullptr);
    glCompileShader(shader);

    GLint success;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
    if (!success) {
        GLint logLength;
        glGetShaderiv(shader, GL_INFO_LOG_LENGTH, &logLength);

        std::vector<char> log(logLength);
        glGetShaderInfoLog(shader, logLength, nullptr, log.data());

        std::string errorLog(log.data(), logLength);

        logger.error("Shader compilation failed\n" + errorLog);
        glDeleteShader(shader);
        throw std::runtime_error("Shader compilation failed: " + errorLog);
    }

    GLuint program = glCreateProgram();
    glAttachShader(program, shader);
    glLinkProgram(program);

    glGetProgramiv(program, GL_LINK_STATUS, &success);
    if (!success) {
        GLint logLength;
        glGetProgramiv(shader, GL_INFO_LOG_LENGTH, &logLength);

        std::vector<char> log(logLength);
        glGetProgramInfoLog(shader, logLength, nullptr, log.data());

        std::string errorLog(log.data(), logLength);
        glDeleteShader(shader);
        logger.error("Program linking failed" + errorLog);
        throw std::runtime_error("Program linking failed" + errorLog);
    }

    glDeleteShader(shader);
    return program;
}

void RenderEngine::pathTracing(RenderTarget& target, const Scene::Camera& camera, const glm::vec3 backgroundColor,
                               int samples) {
    logger.info("Path tracing started");

    glUseProgram(pathTracingProgram);

    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, vertexSSBO);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, texCoordSSBO);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 3, vertexIndexSSBO);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 4, materialSSBO);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 5, materialIndexSSBO);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 6, bvhNodesSSBO);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 7, bvhTrianglesSSBO);
    glBindTextureUnit(8, textureArray);

    glUniform3f(glGetUniformLocation(pathTracingProgram, "uOrigin"), camera.origin.x, camera.origin.y, camera.origin.z);
    glUniform3f(glGetUniformLocation(pathTracingProgram, "uLookAt"), camera.lookAt.x, camera.lookAt.y, camera.lookAt.z);
    glUniform3f(glGetUniformLocation(pathTracingProgram, "uBackgroundColor"), backgroundColor.r, backgroundColor.g,
                backgroundColor.b);
    glUniform1f(glGetUniformLocation(pathTracingProgram, "uFov"), tan(camera.fov / 2.0f));

    glBindImageTexture(0, target.getRawTexture(), 0, GL_FALSE, 0, GL_READ_WRITE, GL_RGBA32F);

    int groupsX = (target.getWidth() + 15) / 16;
    int groupsY = (target.getHeight() + 15) / 16;
    auto start = std::chrono::steady_clock::now();
    for (int i = 1; i <= samples; i++) {
        if (i % 5 == 0 || i == samples) {
            logger.info(std::format("Path tracing progress: {}/{}", i, samples));
        }
        glUniform1ui(glGetUniformLocation(pathTracingProgram, "uSeed"), uniformDistr(gen));
        glUniform1ui(glGetUniformLocation(pathTracingProgram, "uFrameIndex"), i - 1);
        glDispatchCompute(groupsX, groupsY, 1);

        GLenum error = glGetError();
        if (error != 0) {
            logger.error("glDispatchCompute for path tracing failed. Error: " + std::to_string(error));
            throw std::runtime_error("glDispatchCompute for path tracing failed. Error: " + std::to_string(error));
        }
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT);
        glFinish();
    }
    auto end = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    logger.info(std::format("Path tracing finished in {}ms", duration.count()));

    glUseProgram(0);
}

void RenderEngine::fillGbuffer(RenderTarget& target, const GPUData& gpuData, const Scene::Camera& camera) {
    logger.debug("Filling gbuffer");
    glUseProgram(gbufferProgram);
    glBindImageTexture(0, target.getNormalMap(), 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_RGBA32F);
    glBindImageTexture(1, target.getAlbedoMap(), 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_RGBA32F);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, vertexSSBO);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 3, texCoordSSBO);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 4, vertexIndexSSBO);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 5, materialSSBO);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 6, materialIndexSSBO);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 7, bvhNodesSSBO);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 8, bvhTrianglesSSBO);
    glBindTextureUnit(9, textureArray);

    glUniform3f(glGetUniformLocation(gbufferProgram, "uOrigin"), camera.origin.x, camera.origin.y, camera.origin.z);
    glUniform3f(glGetUniformLocation(gbufferProgram, "uLookAt"), camera.lookAt.x, camera.lookAt.y, camera.lookAt.z);
    glUniform1f(glGetUniformLocation(gbufferProgram, "uFov"), tan(camera.fov / 2.0f));
    auto start = std::chrono::steady_clock::now();
    int groupsX = (target.getWidth() + 15) / 16;
    int groupsY = (target.getHeight() + 15) / 16;
    glDispatchCompute(groupsX, groupsY, 1);
    GLenum error = glGetError();
    if (error != 0) {
        logger.error("glDispatchCompute for gbuffer failed. Error: " + std::to_string(error));
        throw std::runtime_error("glDispatchCompute for gbuffer failed. Error: " + std::to_string(error));
    }
    glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT);
    glFinish();
    auto end = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    logger.debug(std::format("gbuffer filling finished in {}ms", duration.count()));
    glUseProgram(0);
}

void RenderEngine::postProcess(RenderTarget& target) const {
    logger.info("Post processing started");
    glUseProgram(postProcessingProgram);
    glBindImageTexture(0, target.getDenoisedTexture(), 0, GL_FALSE, 0, GL_READ_ONLY, GL_RGBA32F);
    glBindImageTexture(1, target.getOutputTexture(), 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_RGBA8);
    auto start = std::chrono::steady_clock::now();
    int groupsX = (target.getWidth() + 15) / 16;
    int groupsY = (target.getHeight() + 15) / 16;
    glDispatchCompute(groupsX, groupsY, 1);
    GLenum error = glGetError();
    if (error != 0) {
        logger.error("glDispatchCompute for post processing failed. Error: " + std::to_string(error));
        throw std::runtime_error("glDispatchCompute for post processing failed. Error: " + std::to_string(error));
    }
    glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT);
    glFinish();
    auto end = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    logger.info(std::format("Post processing finished in {}ms", duration.count()));
    glUseProgram(0);
}

void RenderEngine::uploadGPUBuffers(const GPUData& gpuData, const BVH& bvh) {
    logger.debug("Filling GPU buffers with scene data");
    const auto& vertices = gpuData.vertices;
    const auto& texCoords = gpuData.texCoords;
    const auto& vertexIndices = gpuData.vertexIndices;
    const auto& materials = gpuData.materials;
    const auto& materialIndices = gpuData.materialIndices;
    const auto& bvhNodes = bvh.getNodes();
    const auto& bvhTriangles = bvh.getTriangles();
    logger.debug(std::format("Scene info: \n\tTotal triangles: {}\n\tBVH nodes: {}\n\tBVH depth: {}",
                             vertexIndices.size() / 3, bvhNodes.size(), bvh.getDepth()));

    glBindBuffer(GL_SHADER_STORAGE_BUFFER, vertexSSBO);
    glBufferData(GL_SHADER_STORAGE_BUFFER, vertices.size() * sizeof(glm::vec4), vertices.data(), GL_STATIC_DRAW);

    glBindBuffer(GL_SHADER_STORAGE_BUFFER, texCoordSSBO);
    glBufferData(GL_SHADER_STORAGE_BUFFER, texCoords.size() * sizeof(glm::vec4), texCoords.data(), GL_STATIC_DRAW);

    glBindBuffer(GL_SHADER_STORAGE_BUFFER, vertexIndexSSBO);
    glBufferData(GL_SHADER_STORAGE_BUFFER, vertexIndices.size() * sizeof(int), vertexIndices.data(), GL_STATIC_DRAW);

    glBindBuffer(GL_SHADER_STORAGE_BUFFER, materialSSBO);
    glBufferData(GL_SHADER_STORAGE_BUFFER, materials.size() * sizeof(GPUMaterial), materials.data(), GL_STATIC_DRAW);

    glBindBuffer(GL_SHADER_STORAGE_BUFFER, materialIndexSSBO);
    glBufferData(GL_SHADER_STORAGE_BUFFER, materialIndices.size() * sizeof(int), materialIndices.data(),
                 GL_STATIC_DRAW);

    glBindBuffer(GL_SHADER_STORAGE_BUFFER, bvhNodesSSBO);
    glBufferData(GL_SHADER_STORAGE_BUFFER, bvhNodes.size() * sizeof(BVH::Node), bvhNodes.data(), GL_STATIC_DRAW);

    glBindBuffer(GL_SHADER_STORAGE_BUFFER, bvhTrianglesSSBO);
    glBufferData(GL_SHADER_STORAGE_BUFFER, bvhTriangles.size() * sizeof(int), bvhTriangles.data(), GL_STATIC_DRAW);
}

RenderEngine::GPUData RenderEngine::convertSceneToGPUData(const Scene& scene) {
    logger.debug("Preparing scene data for GPU");
    GPUData data;
    for (const auto& mesh : scene.getMeshes()) {
        int indexOffset = data.vertices.size();
        for (const auto& v : mesh.vertices) data.vertices.push_back(mesh.transform * glm::vec4(v, 1.0));
        for (const auto& uv : mesh.texCoords) data.texCoords.push_back(glm::vec4(uv.x, uv.y, 1.0f, 1.0f));

        for (const auto& primitive : mesh.primitives) {
            for (int i = primitive.startVertexIndex; i < primitive.vertexIndicesCount + primitive.startVertexIndex;
                 i++) {
                data.vertexIndices.push_back(mesh.vertexIndices[i] + indexOffset);
            }
            for (int i = 0; i < primitive.vertexIndicesCount / 3; i++) {
                data.materialIndices.push_back(primitive.materialId);
            }
        }
    }

    for (const auto& material : scene.getMaterials()) {
        GPUMaterial gpuMaterial;
        gpuMaterial.albedo = glm::vec4(material.albedo, 1.0);
        gpuMaterial.emission = glm::vec4(material.emission, 1.0);
        gpuMaterial.metalness = material.metalness;
        gpuMaterial.thicknessFactor = material.thicknessFactor;
        gpuMaterial.attenuationColor = glm::vec4(material.attenuationColor, 1.0);
        gpuMaterial.attenuationDistance = material.attenuationDistance;
        gpuMaterial.roughness = material.roughness;
        gpuMaterial.transmission = material.transmission;
        gpuMaterial.ior = material.ior;
        gpuMaterial.albedoTextureID = material.albedoTextureID;
        data.materials.push_back(gpuMaterial);
    }
    return data;
}

void RenderEngine::loadTextures(const std::vector<Scene::TextureData>& textures) {
    int maxWidth = 1;
    int maxHeight = 1;
    for (const auto& texture : textures) {
        maxWidth = std::max(maxWidth, texture.width);
        maxHeight = std::max(maxHeight, texture.height);
    }
    if (textureArray != 0) {
        glDeleteTextures(1, &textureArray);
        textureArray = 0;
    }

    GLuint error;
    glGenTextures(1, &textureArray);
    error = glGetError();
    if (error) {
        logger.error("glGenTextures for textureArray failed. Error: " + std::to_string(error));
        throw std::runtime_error("glGenTextures for textureArray failed. Error: " + std::to_string(error));
    }

    glBindTexture(GL_TEXTURE_2D_ARRAY, textureArray);
    error = glGetError();
    if (error) {
        logger.error("glBindTexture for textureArray failed. Error: " + std::to_string(error));
        throw std::runtime_error("glBindTexture for textureArray failed. Error: " + std::to_string(error));
    }

    glTexStorage3D(GL_TEXTURE_2D_ARRAY, 1, GL_RGBA8, std::max(1, maxWidth), std::max(1, maxHeight),
                   std::max(1zu, textures.size()));

    error = glGetError();
    if (error) {
        logger.error("glTexStorage3D for textureArray failed. Error: " + std::to_string(error));
        throw std::runtime_error("glTexStorage3D for textureArray failed. Error: " + std::to_string(error));
    }

    int layer = 0;
    for (const auto& texture : textures) {
        if (texture.pixels.empty()) {
            logger.warning("Loading texture with no data");
        }

        glTexSubImage3D(GL_TEXTURE_2D_ARRAY, 0, 0, 0, layer, std::max(1, texture.width), std::max(1, texture.height), 1,
                        GL_RGBA, GL_UNSIGNED_BYTE, texture.pixels.data());
        error = glGetError();
        if (error) {
            logger.error("glTexSubImage3D for textureArray failed. Error: " + std::to_string(error));
            throw std::runtime_error("glTexSubImage3D for textureArray failed. Error: " + std::to_string(error));
        }
        layer++;
    }
    glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_BASE_LEVEL, 0);
    glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAX_LEVEL, 0);

    glBindTexture(GL_TEXTURE_2D_ARRAY, 0);

    logger.debug(std::format("Textures uploaded to GPU: {} layers", layer));
}

void RenderEngine::renderFrame(RenderTarget& target, const Scene& scene, int samples) {
    try {
        logger.info(std::format("Rendering started ({}x{})", target.getWidth(), target.getHeight()));
        ContextGuard context(target);
        glClearTexImage(target.getRawTexture(), 0, GL_RGBA, GL_FLOAT, nullptr);
        glClearTexImage(target.getNormalMap(), 0, GL_RGBA, GL_FLOAT, nullptr);
        glClearTexImage(target.getAlbedoMap(), 0, GL_RGBA, GL_FLOAT, nullptr);
        glClearTexImage(target.getOutputTexture(), 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
        GPUData gpuData = convertSceneToGPUData(scene);
        BVH bvh;
        try {
            bvh = std::move(bvhBuilder.build(gpuData.vertices, gpuData.vertexIndices));
        } catch (const std::exception& e) {
            logger.error(std::format("BVH building failed: {}", e.what()));
            throw;
        }
        auto camera = scene.getCamera();
        auto backgroundColor = scene.getBackgroundColor();
        loadTextures(scene.getTexturesData());
        uploadGPUBuffers(gpuData, bvh);
        pathTracing(target, camera, backgroundColor, samples);

        fillGbuffer(target, gpuData, camera);
        logger.info("Denoising started");
        auto start = std::chrono::steady_clock::now();
        denoiser.denoise(target);
        auto end = std::chrono::steady_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        logger.info(std::format("Denoising finished in {}ms", duration.count()));
        postProcess(target);
    } catch (const std::exception& e) {
        logger.error(std::format("Rendering failed. Reason: {}", e.what()));
    }
}

RenderEngine::~RenderEngine() { destroy(); }