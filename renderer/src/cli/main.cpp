#include <cstdlib>
#include <exception>
#include <filesystem>
#include <iostream>
#include <print>

#include "context-guard.hpp"
#include "logger.hpp"
#include "render-engine.hpp"
#include "scene-loader.hpp"
#include "scene.hpp"
#include "target-manager.hpp"
#include "utils.hpp"

void printHelp(std::string_view programName) {
    std::println("{} - Offline Path Tracer\n", programName);
    std::println("Usage:");
    std::println(" {} <width> <height> <samples> <input_scene> [OPTIONS]\n", programName);
    std::println("Arguments:");
    std::println("  width:             Output image width");
    std::println("  height:            Output image height");
    std::println("  samples:           Path tracer samples");
    std::println("  input_scene:       Path to 3D scene file (only .glb, .gltf supported)");
    std::println("Options:");
    std::println(" -h, --help          Shows this help message");
    std::println(" -o, --output        Output image path (default: output.png)");
    std::println(" -v, --verbose       Print detailed logs");
    std::println(" -d, --debug         Output debug images: raw, albedo, normals");
    std::println(" -p, --plane         Add plane to scene");
    std::println(" -c, --camera        Set camera properties: origin, direction, fov");
    std::println(" -B, --background    Set background color (default: vec3(0,0,0))");
    std::println(" -S, --sun           Set sun properties: color, direction, exponent");
}

void printUsage(std::string_view programName) {
    std::println(std::cerr, "Usage: {} <width> <height> <samples> <input_scene> [OPTIONS]", programName);
    std::println(std::cerr, "Try {} --help for more information", programName);
}

int main(int argc, char* argv[]) {
    if (argc == 2) {
        std::string arg = argv[1];
        if (arg == "-h" || arg == "--help") {
            printHelp(argv[0]);
            return EXIT_SUCCESS;
        }
    }
    if (argc < 5) {
        printUsage(argv[0]);
        return EXIT_FAILURE;
    }

    int width, height, samples;
    std::string input;
    std::string output = "output.png";
    bool debugImages = false;
    bool plane = true;
    glm::vec3 backgroundColor;
    try {
        width = std::stoi(argv[1]);
        height = std::stoi(argv[2]);
        samples = std::stoi(argv[3]);
    } catch (const std::exception& e) {
        std::println(std::cerr, "Error: invalid number format");
        std::println(std::cerr, "  width, height, and samples must be integers");
        printUsage(argv[0]);
        return 1;
    }
    Logger logger("CLI");
    input = argv[4];
    bool showPlane = false;
    float planeSize = 0;
    Scene::Camera userCamera;
    bool cameraSet = false;
    bool sunSet = false;
    Scene::Sun sun;

    for (int i = 5; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "-h" || arg == "--help") {
            printHelp(argv[0]);
            return EXIT_SUCCESS;
        } else if (arg == "-v" || arg == "--verbose")
            logger.showDebug = true;
        else if (arg == "-d" || arg == "--debug")
            debugImages = true;
        else if (arg == "-o" || arg == "--output") {
            if (i + 1 == argc) {
                std::println(std::cerr, "Error: {} requires an argument", arg);
                return EXIT_FAILURE;
            }
            output = argv[++i];
        } else if (arg == "-p" || arg == "--plane") {
            showPlane = true;
            try {
                planeSize = std::stof(argv[++i]);
            } catch (const std::exception& e) {
                std::println(std::cerr, "Error: {} requires number <size:float>", arg);
                return EXIT_FAILURE;
            }
        } else if (arg == "-c" || arg == "--camera") {
            if (i + 7 >= argc) {
                std::println(std::cerr, "Error: {} requires 7 numbers <origin:vec3> <lookAt:vec3> <fov:float>", arg);
                return EXIT_FAILURE;
            }
            try {
                cameraSet = true;
                userCamera.origin.x = std::stof(argv[++i]);
                userCamera.origin.y = std::stof(argv[++i]);
                userCamera.origin.z = std::stof(argv[++i]);
                userCamera.lookAt.x = std::stof(argv[++i]);
                userCamera.lookAt.y = std::stof(argv[++i]);
                userCamera.lookAt.z = std::stof(argv[++i]);
                userCamera.fov = glm::radians(std::stof(argv[++i]));
            } catch (const std::exception& e) {
                std::println(std::cerr, "Error: {} requires 7 numbers <origin:vec3> <lookAt:vec3> <fov:float>", arg);
                return EXIT_FAILURE;
            }
        } else if (arg == "-S" || arg == "--sun") {
            if (i + 7 >= argc) {
                std::println(std::cerr, "Error: {} requires 7 numbers <color:vec3> <direction:vec3> <exponent:float>",
                             arg);
                return EXIT_FAILURE;
            }
            try {
                sunSet = true;
                sun.color.x = std::stof(argv[++i]);
                sun.color.y = std::stof(argv[++i]);
                sun.color.z = std::stof(argv[++i]);
                sun.direction.x = std::stof(argv[++i]);
                sun.direction.y = std::stof(argv[++i]);
                sun.direction.z = std::stof(argv[++i]);
                sun.exponent = std::stof(argv[++i]);
            } catch (const std::exception& e) {
                std::println(std::cerr, "Error: {} requires 7 numbers <color:vec3> <direction:vec3> <exponent:float>",
                             arg);
                return EXIT_FAILURE;
            }
        } else if (arg == "-B" || arg == "--background") {
            if (i + 3 >= argc) {
                std::println(std::cerr, "Error: {} requires 3 numbers <color:vec3>", arg);
                return EXIT_FAILURE;
            }
            try {
                backgroundColor.r = std::stof(argv[++i]);
                backgroundColor.g = std::stof(argv[++i]);
                backgroundColor.b = std::stof(argv[++i]);
            } catch (const std::exception& e) {
                std::println(std::cerr, "Error: {} requires 3 numbers <color:vec3>", arg);
                return EXIT_FAILURE;
            }
        } else {
            std::println(std::cerr, "Unrecognized option: {}", argv[i]);
            std::println(std::cerr, "Try {} --help for more information", argv[0]);
            return EXIT_FAILURE;
        }
    }
    std::filesystem::path outputPath(output);
    std::filesystem::path absoluteDirectoryPath;
    if (outputPath.has_parent_path() && !outputPath.parent_path().empty()) {
        absoluteDirectoryPath = std::filesystem::absolute(outputPath.parent_path());
    } else {
        absoluteDirectoryPath = std::filesystem::current_path();
    }
    std::string outputFilename = outputPath.stem().string();
    try {
        logger.info("Renderer application started");
        TargetManager::init();
        RenderEngine engine;
        SceneLoader loader;
        Scene scene = loader.loadGltfFromFile(input);
        scene.setBackground(backgroundColor);
        if (showPlane) loader.addPlane(scene, planeSize);
        if (cameraSet) scene.setCamera(userCamera);
        if (sunSet) scene.setSun(sun);
        std::shared_ptr<RenderTarget> egl = TargetManager::getInstance().createEGLTarget(width, height);
        engine.renderFrame(*egl, scene, samples);

        auto* eglTarget = dynamic_cast<EglTarget*>(egl.get());
        if (eglTarget) {
            ContextGuard guard(*egl);
            logger.debug(std::format("Writing into {}", (absoluteDirectoryPath / (outputFilename + ".png")).string()));
            utils::writeToPng(egl->getBufferData<uint8_t>(egl->getOutputTexture()), egl->getWidth(), egl->getHeight(),
                              4, absoluteDirectoryPath / (outputFilename + ".png"));
            if (debugImages) {
                logger.debug(
                    std::format("Writing into {}", (absoluteDirectoryPath / (outputFilename + "-raw.png")).string()));
                utils::writeToPng(egl->getBufferData<float>(egl->getRawTexture()), egl->getWidth(), egl->getHeight(), 4,
                                  absoluteDirectoryPath / (outputFilename + "-raw.png"));

                logger.debug(std::format("Writing into {}",
                                         (absoluteDirectoryPath / (outputFilename + "-albedo.png")).string()));
                utils::writeToPng(egl->getBufferData<float>(egl->getAlbedoMap()), egl->getWidth(), egl->getHeight(), 4,
                                  absoluteDirectoryPath / (outputFilename + "-albedo.png"));

                logger.debug(std::format("Writing into {}",
                                         (absoluteDirectoryPath / (outputFilename + "-normal.png")).string()));
                utils::writeToPng(egl->getBufferData<float>(egl->getNormalMap()), egl->getWidth(), egl->getHeight(), 4,
                                  absoluteDirectoryPath / (outputFilename + "-normal.png"));
            }
        }
        logger.info("Renderer application stopped successfully");
        return EXIT_SUCCESS;
    } catch (const std::exception& e) {
        logger.fatal("Application terminated due to error");
        return EXIT_FAILURE;
    }
}
