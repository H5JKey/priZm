#include "scene.hpp"

Scene::Scene() : backgroundColor(0.0f, 0.0f, 0.0f) {}

Scene::Camera Scene::getCamera() const noexcept { return camera; }
glm::vec3 Scene::getBackgroundColor() const noexcept { return backgroundColor; }
Scene::Sun Scene::getSun() const noexcept { return sun; }
const std::vector<Scene::Mesh>& Scene::getMeshes() const noexcept { return meshes; }
const std::vector<Scene::Material>& Scene::getMaterials() const noexcept { return materials; }
const std::vector<Scene::TextureData>& Scene::getTexturesData() const noexcept { return textures; }
void Scene::setCamera(const Scene::Camera& camera) { this->camera = camera; }
void Scene::setBackground(const glm::vec3 backgroundColor) { this->backgroundColor = backgroundColor; }
void Scene::setSun(const Sun& sun) { this->sun = sun; }