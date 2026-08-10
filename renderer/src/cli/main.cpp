#include <cstdlib>
#include <exception>
#include <filesystem>
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
    std::println("  width:         Output image width");
    std::println("  height:        Output image height");
    std::println("  samples:       Path tracer samples");
    std::println("  input_scene:   Path to 3D scene file (only .glb, .gltf supported)");
    std::println("Options:");
    std::println(" -h, --help      Shows this help message");
    std::println(" -o, --output    Output image path (default: output.png)");
    std::println(" -v, --verbose   Print detailed logs");
    std::println(" -d, --debug     Output debug images: raw, albedo, normals");
    std::println(" -p, --plane     Add plane to scene");
    std::println(" -c, --camera    Set camera properties");
    std::println(" -B, --background    Set background color (default: vec3(0,0,0))");
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
    input = argv[4];
    bool showPlane = false;
    float planeSize = 0;
    Scene::Camera userCamera;
    bool cameraSet = false;

    for (int i = 5; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "-h" || arg == "--help") {
            printHelp(argv[0]);
            return EXIT_SUCCESS;
        } else if (arg == "-v" || arg == "--verbose")
            Logger::getInstance().debug = true;
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
        Logger::getInstance().log("Local renderer CLI-application started", Logger::Level::INFO);
        TargetManager::init();
        RenderEngine engine;
        SceneLoader loader;
        Scene scene = loader.loadGltfFromFile(input);
        scene.setBackground(backgroundColor);
        if (showPlane) loader.addPlane(scene, planeSize);
        if (cameraSet) scene.setCamera(userCamera);
        std::shared_ptr<RenderTarget> egl = TargetManager::getInstance().createEGLTarget(width, height);
        engine.renderFrame(*egl, scene, samples);

        auto* eglTarget = dynamic_cast<EglTarget*>(egl.get());
        if (eglTarget) {
            ContextGuard guard(*egl);
            Logger::getInstance().log(
                std::format("Writing into {}", (absoluteDirectoryPath / (outputFilename + ".png")).string()),
                Logger::Level::DEBUG);
            utils::writeToPng(egl->getBufferData<uint8_t>(egl->getOutputTexture()), egl->getWidth(), egl->getHeight(),
                              4, absoluteDirectoryPath / (outputFilename + ".png"));
            if (debugImages) {
                Logger::getInstance().log(
                    std::format("Writing into {}", (absoluteDirectoryPath / (outputFilename + "-raw.png")).string()),
                    Logger::Level::DEBUG);
                utils::writeToPng(egl->getBufferData<float>(egl->getRawTexture()), egl->getWidth(), egl->getHeight(), 4,
                                  absoluteDirectoryPath / (outputFilename + "-raw.png"));

                Logger::getInstance().log(
                    std::format("Writing into {}", (absoluteDirectoryPath / (outputFilename + "-albedo.png")).string()),
                    Logger::Level::DEBUG);
                utils::writeToPng(egl->getBufferData<float>(egl->getAlbedoMap()), egl->getWidth(), egl->getHeight(), 4,
                                  absoluteDirectoryPath / (outputFilename + "-albedo.png"));

                Logger::getInstance().log(
                    std::format("Writing into {}", (absoluteDirectoryPath / (outputFilename + "-normal.png")).string()),
                    Logger::Level::DEBUG);
                utils::writeToPng(egl->getBufferData<float>(egl->getNormalMap()), egl->getWidth(), egl->getHeight(), 4,
                                  absoluteDirectoryPath / (outputFilename + "-normal.png"));
            }
        }
        Logger::getInstance().log("Renderer application stopped successfully", Logger::Level::INFO);
        return EXIT_SUCCESS;
    } catch (const std::exception& e) {
        Logger::getInstance().log("Application terminated due to error", Logger::Level::FATAL);
        return EXIT_FAILURE;
    }
}
