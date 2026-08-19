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

Logger logger("WORKER");
int main() try {
    env::dotenv dotenv(".env");
    Config config;
    config.apply(dotenv);
    config.fromEnvironment();

    Logger::showDebug = config.logDebug();
    Logger::setMinLevel(config.logLevel());

    Aws::InitAPI(options);
    logger.debug(std::format("Aws initialized"));
    TargetManager::init();
    RenderEngine engine;
    SceneLoader sceneLoader;

    S3Client s3client(config.s3Host(), Aws::Auth::AWSCredentials(config.s3AccessKey(), config.s3SecretKey()));
    KafkaConsumer consumer(config.kafkaHost(), config.kafkaGroupID(), config.kafkaTopicInput());
    KafkaProducer producer(config.kafkaHost());
    logger.info("Renderer-worker started");

    while (true) {
        json inputJson;
        int width, height, samples;
        int project_id;
        std::string bucket, key;
        std::string modelName;
        try {
            logger.info(std::format("Listening for messages..."));
            std::string message = consumer.consume();
            logger.info(std::format("Message processing started"));
            try {
                inputJson = json::parse(message);
                width = inputJson["render"]["width"];
                height = inputJson["render"]["height"];
                samples = inputJson["render"]["samples"];
                project_id = inputJson["project_id"];
                bucket = inputJson["file"]["bucket"];
                key = inputJson["file"]["key"];
            } catch (const std::exception& e) {
                logger.error(std::format("Failed to parse json from string: {}. Error: {}", message, e.what()));
                throw;
            }
            std::vector<uint8_t> data;
            data = s3client.getData(bucket, key);

            Scene scene = sceneLoader.loadGltfFromMemory(data);
            scene.setBackground(glm::vec3(0.53, 0.81, 0.92));
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
                    {"key", outputKey},
                };
            } catch (const std::exception& e) {
                logger.error(std::format("Failed to generate output json: {}", e.what()));
                throw;
            }

            producer.produce(config.kafkaTopicOutput(), outputJson.dump());
            consumer.commit();
        } catch (const std::exception& e) {
            logger.error(std::format("Processing message: (offset = {}, partition = {}) failed. Reason: {}",
                                     consumer.lastMessage.value().get_offset(),
                                     consumer.lastMessage.value().get_partition(), e.what()));
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
        logger.info(std::format("Current message processing finished successfully"));
    }
    logger.info("Renderer worker stopped successfully");
    Aws::ShutdownAPI(options);
    return EXIT_SUCCESS;
} catch (const env::dotenv::ParseError& e) {
    logger.error(std::format("Failed to parse .env file '{}' at line {}. Error: {}", e.filename, e.line, e.what()));
    return EXIT_FAILURE;
} catch (const std::exception& e) {
    Aws::ShutdownAPI(options);
    logger.fatal(std::format("Worker terminated due to error: {}", e.what()));
    return EXIT_FAILURE;
}
