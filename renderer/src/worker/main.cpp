#include <aws/core/Aws.h>

#include <cstdlib>
#include <exception>
#include <filesystem>
#include <nlohmann/json.hpp>

#include "config.hpp"
#include "context-guard.hpp"
#include "dotenv.hpp"
#include "kafka-consumer.hpp"
#include "kafka-producer.hpp"
#include "logger.hpp"
#include "render-engine.hpp"
#include "s3-client.hpp"
#include "scene-loader.hpp"
#include "scene.hpp"
#include "target-manager.hpp"
#include "utils.hpp"

using json = nlohmann::json;

Aws::SDKOptions options;

std::vector<uint8_t> renderPipeline(RenderEngine& engine, Scene scene, int width, int height, int samples) {
    std::shared_ptr<RenderTarget> egl = TargetManager::getInstance().createEGLTarget(width, height);
    engine.renderFrame(*egl, scene, samples);
    ContextGuard guard(*egl);
    auto data = egl->getBufferData<uint8_t>(egl->getOutputTexture());
    return utils::writeToPng(data, width, height, 4);
}

int main() try {
    env::dotenv dotenv(".env");
    Config config;
    config.apply(dotenv);
    config.fromEnvironment();

    Aws::InitAPI(options);
    Logger::getInstance().debug = config.logDebug();

    Logger::getInstance().setMinLevel(config.logLevel());

    Logger::getInstance().log(std::format("Aws initialized"), Logger::Level::DEBUG);
    TargetManager::init();
    RenderEngine engine;
    SceneLoader sceneLoader;

    S3Client s3client(config.s3Host(), Aws::Auth::AWSCredentials(config.s3AccessKey(), config.s3SecretKey()));
    KafkaConsumer consumer(config.kafkaHost(), config.kafkaGroupID(), config.kafkaTopicInput());
    KafkaProducer producer(config.kafkaHost());
    Logger::getInstance().log("Renderer worker started", Logger::Level::INFO);

    while (true) {
        json inputJson;
        int width, height, samples;
        int project_id;
        std::string bucket, key;
        std::string modelName;
        try {
            Logger::getInstance().log(std::format("Listening for messages..."), Logger::Level::INFO);
            std::string message = consumer.consume();
            Logger::getInstance().log(std::format("Message processing started"), Logger::Level::INFO);
            try {
                inputJson = json::parse(message);
                width = inputJson["render"]["width"];
                height = inputJson["render"]["height"];
                samples = inputJson["render"]["samples"];
                project_id = inputJson["project_id"];
                bucket = inputJson["file"]["bucket"];
                key = inputJson["file"]["key"];
                // modelName = inputJson["file"]["name"];
            } catch (const std::exception& e) {
                Logger::getInstance().log(
                    std::format("Failed to parse json from string: {}. Error: {}", message, e.what()),
                    Logger::Level::ERROR);
                throw;
            }
            std::vector<uint8_t> data;
            data = s3client.getData(bucket, key);

            Scene scene = sceneLoader.loadGltfFromMemory(data);
            std::vector<uint8_t> output;
            if (config.preview())
                output = std::move(renderPipeline(engine, scene, 200, 200 * (static_cast<float>(height) / width), 5));
            else
                output = std::move(renderPipeline(engine, scene, width, height, samples));
            std::string outputKey = key;
            auto dotPos = outputKey.rfind('.');
            if (dotPos != std::string::npos) {
                outputKey = outputKey.substr(0, dotPos);
            }
            if (config.preview())
                outputKey += "_preview.png";
            else
                outputKey += ".png";

            s3client.putData(output, config.s3BucketOutput(), outputKey);

            json outputJson;
            try {
                outputJson["project_id"] = project_id;
                outputJson["file"] = {
                    {"bucket", config.s3BucketOutput()},
                    {"name", "67"},
                    {"key", outputKey},
                    {"size", 67},
                };
            } catch (const std::exception& e) {
                Logger::getInstance().log(std::format("Failed to generate output json: {}", e.what()),
                                          Logger::Level::ERROR);
                throw;
            }

            producer.produce(config.kafkaTopicOutput(), outputJson.dump());
            consumer.commit();
        } catch (const std::exception& e) {
            Logger::getInstance().log(
                std::format("Processing message: (offset = {}, partition = {}) failed. Reason: {}",
                            consumer.lastMessage.value().get_offset(), consumer.lastMessage.value().get_partition(),
                            e.what()),
                Logger::Level::ERROR);
            int retries = 0;
            if (inputJson.contains("retry_count")) {
                retries = inputJson["retry_count"];
            }
            if (retries < config.maxRetries()) {
                inputJson["retry_count"] = ++retries;
                producer.produce(config.kafkaTopicInput(), inputJson.dump());
            } else {
                json deadLetter;
                deadLetter["project_id"] = project_id;
                deadLetter["reason"] = e.what();
                producer.produce(config.kafkaTopicDLQ(), deadLetter.dump());
            }
            consumer.commit();
            continue;
        }
        Logger::getInstance().log(std::format("Current message processing finished successfully"), Logger::Level::INFO);
    }
    Logger::getInstance().log("Renderer application stopped successfully", Logger::Level::INFO);
    Aws::ShutdownAPI(options);
    return EXIT_SUCCESS;
} catch (const env::dotenv::ParseError& e) {
    Logger::getInstance().log(
        std::format("Failed to parse .env file '{}' at line {}. Error: {}", e.filename, e.line, e.what()),
        Logger::Level::ERROR);
    return EXIT_FAILURE;
} catch (const std::exception& e) {
    Aws::ShutdownAPI(options);
    Logger::getInstance().log(std::format("Application terminated due to error: {}", e.what()), Logger::Level::FATAL);
    return EXIT_FAILURE;
}
