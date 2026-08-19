#include "scene-loader.hpp"

#include <stb_image.h>

#include <exception>
#include <filesystem>
#include <format>
#include <glm/glm.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <stdexcept>
#include <variant>
#include <vector>

#include "fastgltf/core.hpp"
#include "fastgltf/types.hpp"
#include "utils.hpp"

SceneLoader::SceneLoader() : parser(supportedExtensions), logger("SCENE") {}

Scene::TextureData SceneLoader::loadTexture(const fastgltf::Image& image, const fastgltf::Asset& asset) const {
    try {
        return std::visit(
            fastgltf::visitor{
                [&](const fastgltf::sources::URI& filePath) -> Scene::TextureData {
                    assert(filePath.fileByteOffset == 0);
                    if (!filePath.uri.isLocalPath()) {
                        throw std::runtime_error("Non-local URI not supported");
                    }

                    const std::string path(filePath.uri.path().begin(), filePath.uri.path().end());
                    std::vector<uint8_t> result;
                    int width, height, channels;
                    utils::readImage(path, width, height, channels, result);

                    return Scene::TextureData{.pixels = std::move(result), .width = width, .height = height};
                },
                [&](const fastgltf::sources::Array& vector) -> Scene::TextureData {
                    std::vector<uint8_t> result;
                    int width, height, channels;

                    utils::readImageFromMemory(vector.bytes.data(), vector.bytes.size(), width, height, channels,
                                               result);

                    return Scene::TextureData{.pixels = std::move(result), .width = width, .height = height};
                },
                [&](const fastgltf::sources::BufferView& view) -> Scene::TextureData {
                    auto& bufferView = asset.bufferViews[view.bufferViewIndex];
                    auto& buffer = asset.buffers[bufferView.bufferIndex];
                    return std::visit(
                        fastgltf::visitor{
                            [&](const fastgltf::sources::Array& vector) -> Scene::TextureData {
                                std::vector<uint8_t> result;
                                int width, height, channels;
                                const auto* data = vector.bytes.data() + bufferView.byteOffset;
                                const auto size = bufferView.byteLength;

                                utils::readImageFromMemory(data, size, width, height, channels, result);
                                return Scene::TextureData{
                                    .pixels = std::move(result), .width = width, .height = height};
                            },
                            [](auto& arg) -> Scene::TextureData {
                                throw std::runtime_error(std::string("Unsupported format: ") + typeid(arg).name());
                            },
                        },
                        buffer.data);
                },
                [](auto& arg) -> Scene::TextureData {
                    throw std::runtime_error(std::string("Unsupported format: ") + typeid(arg).name());
                },
            },
            image.data);
    } catch (const std::exception& e) {
        logger.error(std::format("Failed to load texture {}: {}", image.name, e.what()));
        throw;
    }
}

Scene::Material SceneLoader::loadMaterial(const fastgltf::Material& gltfMaterial,
                                          std::vector<Scene::TextureData>& textures,
                                          const fastgltf::Asset& asset) const {
    Scene::Material material;

    material.metalness = gltfMaterial.pbrData.metallicFactor;
    material.albedo = glm::make_vec4(gltfMaterial.pbrData.baseColorFactor.data());
    material.roughness = gltfMaterial.pbrData.roughnessFactor;
    material.ior = gltfMaterial.ior;

    if (gltfMaterial.volume) {
        material.attenuationColor = glm::make_vec4(gltfMaterial.volume->attenuationColor.data());
        material.attenuationDistance = gltfMaterial.volume->attenuationDistance;
        material.thicknessFactor = gltfMaterial.volume->thicknessFactor;
    } else {
        material.attenuationColor = glm::vec3(1.0);
        material.attenuationDistance = 0.01;
        material.thicknessFactor = 0.01;
    }

    material.transmission = 0.0f;
    if (gltfMaterial.transmission) {
        material.transmission = gltfMaterial.transmission->transmissionFactor;
    }

    glm::vec3 emissiveColor = glm::make_vec3(gltfMaterial.emissiveFactor.data());
    float emissiveStrength = gltfMaterial.emissiveStrength;
    material.emission = emissiveColor * emissiveStrength;

    material.albedoTextureID = -1;
    if (gltfMaterial.pbrData.baseColorTexture.has_value()) {
        auto& texInfo = gltfMaterial.pbrData.baseColorTexture.value();
        auto textureIndex = texInfo.textureIndex;

        if (textureIndex < asset.textures.size()) {
            auto& gltfTexture = asset.textures[textureIndex];
            auto imageIndex = gltfTexture.imageIndex;

            if (imageIndex.has_value() && imageIndex.value() < asset.images.size()) {
                auto& image = asset.images[imageIndex.value()];
                Scene::TextureData texture;
                try {
                    texture = std::move(loadTexture(image, asset));
                } catch (const std::exception& e) {
                    logger.error(
                        std::format("Failed to load texture for material '{}': {}", gltfMaterial.name, e.what()));
                    throw;
                }
                texture.id = static_cast<int>(textures.size());

                textures.push_back(std::move(texture));
                material.albedoTextureID = texture.id;
            }
        }
    }
    return material;
}

Scene::Camera SceneLoader::loadCamera(const fastgltf::Camera::Perspective& gltfCamera,
                                      const fastgltf::Node& node) const {
    logger.debug("Loading camera");
    Scene::Camera camera;

    glm::mat4 worldMatrix(1.0f);
    if (auto* trs = std::get_if<fastgltf::TRS>(&node.transform)) {
        auto translation = glm::vec3(trs->translation.x(), trs->translation.y(), trs->translation.z());
        auto rotation = glm::quat(trs->rotation.w(), trs->rotation.x(), trs->rotation.y(), trs->rotation.z());
        auto scale = glm::vec3(trs->scale.x(), trs->scale.y(), trs->scale.z());
        worldMatrix = glm::translate(glm::mat4(1.0f), translation) * glm::mat4_cast(rotation) *
                      glm::scale(glm::mat4(1.0f), scale);
    }
    camera.origin = glm::vec4(worldMatrix[3].x, worldMatrix[3].y, worldMatrix[3].z, 1.0);

    camera.fov = gltfCamera.yfov;
    glm::vec3 direction = glm::mat3(worldMatrix) * glm::vec3(0.0f, 0.0f, -1.0f);
    direction = glm::normalize(direction);

    camera.lookAt = glm::vec4(glm::vec3(camera.origin) + direction, 1.0);
    return camera;
}

void SceneLoader::loadNode(const fastgltf::Node& node, const fastgltf::Asset& asset, Scene& scene,
                           glm::mat4 parentTransform) const {
    glm::mat4 localTransform = glm::mat4(1.0f);

    if (auto* trs = std::get_if<fastgltf::TRS>(&node.transform)) {
        auto translation = glm::vec3(trs->translation.x(), trs->translation.y(), trs->translation.z());
        auto rotation = glm::quat(trs->rotation.w(), trs->rotation.x(), trs->rotation.y(), trs->rotation.z());
        auto scale = glm::vec3(trs->scale.x(), trs->scale.y(), trs->scale.z());
        localTransform = glm::translate(glm::mat4(1.0f), translation) * glm::mat4_cast(rotation) *
                         glm::scale(glm::mat4(1.0f), scale);
    }

    glm::mat4 transform = parentTransform * localTransform;

    /* Loading meshes*/
    if (node.meshIndex.has_value()) {
        const auto& gltfMesh = asset.meshes[node.meshIndex.value()];
        Scene::Mesh mesh = loadMesh(gltfMesh, asset);
        mesh.transform = transform;
        scene.meshes.push_back(std::move(mesh));
    }
    for (const auto& child : node.children) {
        loadNode(asset.nodes[child], asset, scene, transform);
    }
}

Scene::Mesh SceneLoader::loadMesh(const fastgltf::Mesh& gltfMesh, const fastgltf::Asset& asset) const {
    Scene::Mesh mesh;
    try {
        for (int i = 0; i < gltfMesh.primitives.size(); i++) {
            const auto& gltfPrimitive = gltfMesh.primitives[i];
            Scene::Mesh::Primitive primitive;
            if (gltfPrimitive.materialIndex.has_value())
                primitive.materialId = gltfPrimitive.materialIndex.value();
            else
                primitive.materialId = 0;

            const auto* positionIt = gltfPrimitive.findAttribute("POSITION");
            if (positionIt == gltfPrimitive.attributes.end()) {
                throw std::runtime_error(std::format("Failed to find POSITION attribute for primitive {}", i));
            }
            const auto& positionAccessor = asset.accessors[positionIt->accessorIndex];
            if (!positionAccessor.bufferViewIndex.has_value()) {
                throw std::runtime_error(std::format("No value at bufferViewIndex for primitive {}", i));
            }
            size_t vertexCount = positionAccessor.count;
            size_t startVertex = mesh.vertices.size();

            mesh.vertices.resize(startVertex + vertexCount);
            fastgltf::iterateAccessorWithIndex<fastgltf::math::fvec3>(
                asset, positionAccessor, [&](fastgltf::math::fvec3 pos, std::size_t idx) {
                    size_t vertexIdx = startVertex + idx;
                    mesh.vertices[vertexIdx] = glm::vec4(pos.x(), pos.y(), pos.z(), 1.0f);
                });

            const auto* texCoordIt = gltfPrimitive.findAttribute("TEXCOORD_0");
            if (texCoordIt != gltfPrimitive.attributes.end()) {
                const auto& texCoordAccessor = asset.accessors[texCoordIt->accessorIndex];
                if (!texCoordAccessor.bufferViewIndex.has_value()) {
                    throw std::runtime_error(std::format("No value at bufferViewIndex for primitive {}", i));
                }
                size_t startTexCoord = mesh.texCoords.size();

                mesh.texCoords.resize(startTexCoord + texCoordAccessor.count);
                fastgltf::iterateAccessorWithIndex<fastgltf::math::fvec2>(
                    asset, texCoordAccessor, [&](fastgltf::math::fvec2 uv, std::size_t idx) {
                        size_t texIdx = startTexCoord + idx;
                        mesh.texCoords[texIdx] = glm::vec4(uv.x(), uv.y(), 1.0f, 1.0f);
                    });
            } else {
                mesh.texCoords.insert(mesh.texCoords.end(), vertexCount, glm::vec2(0.0f));
            }
            if (!gltfPrimitive.indicesAccessor.has_value()) {
                throw std::runtime_error(std::format("No value at indicesAccessor for primitive", i));
            }
            const auto& indexAccessor = asset.accessors[gltfPrimitive.indicesAccessor.value()];
            size_t startIndex = mesh.vertexIndices.size();
            primitive.startVertexIndex = startIndex;
            primitive.vertexIndicesCount = indexAccessor.count;
            mesh.vertexIndices.resize(startIndex + indexAccessor.count);

            if (indexAccessor.componentType == fastgltf::ComponentType::UnsignedShort) {
                std::vector<uint16_t> tmp(indexAccessor.count);
                fastgltf::copyFromAccessor<uint16_t>(asset, indexAccessor, tmp.data());
                for (size_t i = 0; i < indexAccessor.count; ++i) {
                    mesh.vertexIndices[startIndex + i] = tmp[i] + startVertex;
                }
            } else {
                std::vector<uint32_t> tmp(indexAccessor.count);
                fastgltf::copyFromAccessor<uint32_t>(asset, indexAccessor, tmp.data());
                for (size_t i = 0; i < indexAccessor.count; ++i) {
                    mesh.vertexIndices[startIndex + i] = tmp[i] + startVertex;
                }
            }
            mesh.primitives.push_back(std::move(primitive));
        }
    } catch (const std::exception& e) {
        logger.error(std::format("Failed to load mesh {}: {}", gltfMesh.name, e.what()));
        throw;
    }
    return mesh;
}

Scene SceneLoader::loadGltfFromFile(const std::filesystem::path& path) {
    logger.debug(std::format("Loading scene from file {}", path.string()));
    if (!std::filesystem::exists(path)) {
        logger.error(std::format("Failed to find {} ", path.string()));
        throw std::runtime_error(std::format("Failed to find {} ", path.string()));
    }

    auto data = fastgltf::GltfDataBuffer::FromPath(path);
    if (auto error = data.error(); error != fastgltf::Error::None) {
        logger.error(std::format("Failed to load {}. Error: {} ", path.string(), fastgltf::getErrorMessage(error)));
        throw std::runtime_error(
            std::format("Failed to load {}. Error: {} ", path.string(), fastgltf::getErrorMessage(error)));
    }
    auto asset = parser.loadGltf(data.get(), path.parent_path(), gltfOptions);
    if (auto error = asset.error(); error != fastgltf::Error::None) {
        logger.error(std::format("Failed to load {}. Error: {} ", path.string(), fastgltf::getErrorMessage(error)));
        throw std::runtime_error(
            std::format("Failed to load {}. Error: {} ", path.string(), fastgltf::getErrorMessage(error)));
    }
    return loadGltf(asset.get());
}

Scene SceneLoader::loadGltfFromMemory(const std::vector<uint8_t>& bytes) {
    logger.debug(std::format("Loading scene from memory. Size: {}", bytes.size()));
    auto data = fastgltf::GltfDataBuffer::FromBytes(reinterpret_cast<const std::byte*>(bytes.data()), bytes.size());
    if (auto error = data.error(); error != fastgltf::Error::None) {
        logger.error(std::format("Failed to load data from memory. Error: {} ", fastgltf::getErrorMessage(error)));
        throw std::runtime_error(
            std::format("Failed to load data from memory. Error: {} ", fastgltf::getErrorMessage(error)));
    }
    auto asset = parser.loadGltf(data.get(), ".", gltfOptions);
    if (auto error = asset.error(); error != fastgltf::Error::None) {
        logger.error(std::format("Failed to load data from memory. Error: {} ", fastgltf::getErrorMessage(error)));
        throw std::runtime_error(
            std::format("Failed to load data from meory. Error: {} ", fastgltf::getErrorMessage(error)));
    }
    return loadGltf(asset.get());
}

Scene SceneLoader::loadGltf(const fastgltf::Asset& asset) {
    Scene scene;

    /* Loading nodes recursively*/
    logger.debug("Loading nodes");
    const fastgltf::Scene& gltfScene = asset.scenes[asset.defaultScene.value()];
    for (std::size_t rootIdx : gltfScene.nodeIndices) {
        const fastgltf::Node& root = asset.nodes[rootIdx];
        loadNode(root, asset, scene);
    }

    /* Loading camera */
    bool cameraFound = false;
    for (auto node : asset.nodes) {
        if (node.cameraIndex.has_value()) {
            auto* gltfCamera =
                std::get_if<fastgltf::Camera::Perspective>(&asset.cameras[node.cameraIndex.value()].camera);
            if (gltfCamera) {
                scene.camera = loadCamera(*gltfCamera, node);
                cameraFound = true;
                break;
            }
        }
    }
    if (!cameraFound) {
        logger.warning("Camera was not found in file. Default camera will be applied");
        glm::vec3 boxMax(-std::numeric_limits<float>::infinity()), boxMin(std::numeric_limits<float>::infinity());
        bool empty = true;
        for (const auto& mesh : scene.getMeshes()) {
            for (auto v : mesh.vertices) {
                v = glm::vec3(mesh.transform * glm::vec4(v, 1.0));
                empty = false;
                boxMax = glm::max(boxMax, v);
                boxMin = glm::min(boxMin, v);
            }
        }
        if (!empty) {
            glm::vec3 center = (boxMin + boxMax) / 2.0f;
            glm::vec3 size = boxMax - boxMin;
            scene.camera.fov = glm::radians(70.f);

            float maxSize = std::max(size.x, std::max(size.y, size.z));

            float distance = (maxSize * 0.5f) / std::tan(scene.camera.fov * 0.5f);

            scene.camera.origin = center + glm::normalize(glm::vec3(1.0f, 0.7f, 1.0f)) * 2.0f * distance;
            scene.camera.lookAt = center;
        } else {
            scene.camera.origin = glm::vec3(1, 0, 0);
            scene.camera.lookAt = glm::vec3(0, 0, 0);
            scene.camera.fov = glm::radians(70.f);
        }
    }

    /* Loading materials */
    for (const auto& material : asset.materials) {
        scene.materials.push_back(loadMaterial(material, scene.textures, asset));
    }
    logger.info(std::format("Scene loaded. Meshes: {}, Materials: {}, Textures: {}", scene.meshes.size(),
                            scene.materials.size(), scene.textures.size()));
    return scene;
}

void SceneLoader::addPlane(Scene& scene, float planeSize) {
    glm::vec3 boxMax(-std::numeric_limits<float>::infinity()), boxMin(std::numeric_limits<float>::infinity());
    bool empty = true;
    for (const auto& mesh : scene.getMeshes()) {
        for (auto v : mesh.vertices) {
            v = glm::vec3(mesh.transform * glm::vec4(v, 1.0));
            empty = false;
            boxMax = glm::max(boxMax, v);
            boxMin = glm::min(boxMin, v);
        }
    }
    glm::vec3 center;
    if (!empty) {
        center = (boxMin + boxMax) / 2.0f;
    } else {
        center = glm::vec3(0, 0, 0);
    }
    Scene::Mesh planeMesh;
    planeMesh.transform = glm::mat4(1.0);
    planeMesh.vertices = {glm::vec3(center.x - planeSize, boxMin.y, center.z + planeSize),
                          glm::vec3(center.x - planeSize, boxMin.y, center.z - planeSize),
                          glm::vec3(center.x + planeSize, boxMin.y, center.z - planeSize),
                          glm::vec3(center.x + planeSize, boxMin.y, center.z + planeSize)};
    planeMesh.vertexIndices = {3, 1, 0, 2, 1, 3};

    Scene::Mesh::Primitive primitive1, primitive2;
    primitive1.startVertexIndex = 0;
    primitive1.vertexIndicesCount = 3;
    primitive2.startVertexIndex = 3;
    primitive2.vertexIndicesCount = 3;
    scene.materials.push_back(Scene::Material());
    primitive1.materialId = scene.materials.size() - 1;
    primitive2.materialId = scene.materials.size() - 1;

    planeMesh.primitives.push_back(primitive1);
    planeMesh.primitives.push_back(primitive2);

    scene.meshes.push_back(planeMesh);
}
