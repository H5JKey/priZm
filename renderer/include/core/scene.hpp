#pragma once
#include <glm/ext/matrix_float4x4.hpp>
#include <glm/ext/vector_float4.hpp>
#include <glm/glm.hpp>
#include <print>
#include <vector>
class SceneLoader;

class Scene {
   public:
    struct Mesh {
        struct Primitive {
            int startVertexIndex;
            int vertexIndicesCount;
            int materialId;

            Primitive() : startVertexIndex(0), vertexIndicesCount(0), materialId(-1) {}
        };
        std::vector<int> vertexIndices;
        std::vector<glm::vec3> vertices;
        std::vector<glm::vec2> texCoords;
        glm::mat4 transform;
        std::vector<Primitive> primitives;

        Mesh() : transform(glm::mat4(1.0f)) {}
    };

    struct TextureData {
        std::vector<uint8_t> pixels;
        int width = 0;
        int height = 0;
        int id = -1;
    };

    struct Material {
        glm::vec3 albedo;
        glm::vec3 emission;
        glm::vec3 attenuationColor;
        float attenuationDistance;
        float thicknessFactor;
        float metalness;
        float roughness;
        float transmission;
        float ior;
        int albedoTextureID;

        Material()
            : albedo(glm::vec3(0.3f, 0.45f, 0.3f)),
              emission(glm::vec3(0.0)),
              thicknessFactor(0.0),
              attenuationDistance(1.0),
              attenuationColor(glm::vec3(0.0)),
              metalness(0.0),
              roughness(0.5),
              transmission(0.0),
              ior(1.5),
              albedoTextureID(-1) {}
    };

    struct Camera {
        Camera() : origin(glm::vec3(1, 0, 0)), lookAt(glm::vec3(0, 0, 0)), fov(glm::radians(70.f)) {}
        glm::vec3 origin;
        glm::vec3 lookAt;
        float fov;
    };

   private:
    friend class SceneLoader;

    Camera camera;
    std::vector<Mesh> meshes;
    std::vector<Material> materials;
    glm::vec3 backgroundColor;
    std::vector<TextureData> textures;

   public:
    Scene();
    Camera getCamera() const noexcept;
    glm::vec3 getBackgroundColor() const noexcept;
    const std::vector<Mesh>& getMeshes() const noexcept;
    const std::vector<Material>& getMaterials() const noexcept;
    const std::vector<TextureData>& getTexturesData() const noexcept;
    void setCamera(const Camera& camera);
    void setBackground(const glm::vec3 backgroundColor);
};