#include "config.hpp"

#include <stdexcept>

void Config::apply(env::dotenv dotenv) {
    try {
        if (dotenv.hasVariable("KAFKA_HOST")) kafkaHost_ = dotenv["KAFKA_HOST"];
        if (dotenv.hasVariable("KAFKA_GROUP_ID")) kafkaGroupID_ = dotenv["KAFKA_GROUP_ID"];
        if (dotenv.hasVariable("KAFKA_TOPIC_INPUT")) kafkaTopicInput_ = dotenv["KAFKA_TOPIC_INPUT"];
        if (dotenv.hasVariable("KAFKA_TOPIC_OUTPUT")) kafkaTopicOutput_ = dotenv["KAFKA_TOPIC_OUTPUT"];
        if (dotenv.hasVariable("KAFKA_TOPIC_DLQ")) kafkaTopicDLQ_ = dotenv["KAFKA_TOPIC_DLQ"];
        if (dotenv.hasVariable("MAX_RETRIES")) maxRetries_ = dotenv["MAX_RETRIES"];
        if (dotenv.hasVariable("S3_HOST")) s3Host_ = dotenv["S3_HOST"];
        if (dotenv.hasVariable("S3_ACCESS_KEY")) s3AccessKey_ = dotenv["S3_ACCESS_KEY"];
        if (dotenv.hasVariable("S3_SECRET_KEY")) s3SecretKey_ = dotenv["S3_SECRET_KEY"];
        if (dotenv.hasVariable("S3_BUCKET_INPUT")) s3BucketInput_ = dotenv["S3_BUCKET_INPUT"];
        if (dotenv.hasVariable("S3_BUCKET_OUTPUT")) s3BucketOutput_ = dotenv["S3_BUCKET_OUTPUT"];
        if (dotenv.hasVariable("RENDERER_LOG_LEVEL"))
            logLevel_ = Logger::getLevelFromString(dotenv["RENDERER_LOG_LEVEL"]);
        if (dotenv.hasVariable("RENDERER_LOG_DEBUG")) logDebug_ = dotenv["RENDERER_LOG_DEBUG"];
        if (dotenv.hasVariable("RENDERER_PREVIEW")) preview_ = dotenv["RENDERER_PREVIEW"];
    } catch (const env::Value::ValueError& e) {
        throw std::runtime_error(std::format("Invalid value format in .env file. Error: {}.", e.what()));
    }
}

void Config::fromEnvironment() {
    try {
        if (char* ptr = std::getenv("KAFKA_HOST")) kafkaHost_ = env::Value(ptr);
        if (char* ptr = std::getenv("KAFKA_GROUP_ID")) kafkaGroupID_ = env::Value(ptr);
        if (char* ptr = std::getenv("KAFKA_TOPIC_INPUT")) kafkaTopicInput_ = env::Value(ptr);
        if (char* ptr = std::getenv("KAFKA_TOPIC_OUTPUT")) kafkaTopicOutput_ = env::Value(ptr);
        if (char* ptr = std::getenv("KAFKA_TOPIC_DLQ")) kafkaTopicDLQ_ = env::Value(ptr);
        if (char* ptr = std::getenv("MAX_RETRIES")) maxRetries_ = env::Value(ptr);
        if (char* ptr = std::getenv("S3_HOST")) s3Host_ = env::Value(ptr);
        if (char* ptr = std::getenv("S3_ACCESS_KEY")) s3AccessKey_ = env::Value(ptr);
        if (char* ptr = std::getenv("S3_SECRET_KEY")) s3SecretKey_ = env::Value(ptr);
        if (char* ptr = std::getenv("S3_BUCKET_INPUT")) s3BucketInput_ = env::Value(ptr);
        if (char* ptr = std::getenv("S3_BUCKET_OUTPUT")) s3BucketOutput_ = env::Value(ptr);
        if (char* ptr = std::getenv("RENDERER_LOG_LEVEL")) logLevel_ = Logger::getLevelFromString(env::Value(ptr));
        if (char* ptr = std::getenv("RENDERER_LOG_DEBUG")) logDebug_ = env::Value(ptr);
        if (char* ptr = std::getenv("RENDERER_PREVIEW")) preview_ = env::Value(ptr);
    } catch (const env::Value::ValueError& e) {
        throw std::runtime_error(std::format("Invalid environment variable value format. Error: {}.", e.what()));
    }
}

std::string Config::kafkaHost() const {
    if (!kafkaHost_.has_value()) {
        throw std::runtime_error("KAFKA_HOST not configured");
    }
    return kafkaHost_.value();
}

std::string Config::kafkaGroupID() const {
    if (!kafkaGroupID_.has_value()) {
        throw std::runtime_error("KAFKA_GROUP_ID not configured");
    }
    return kafkaGroupID_.value();
}

std::string Config::kafkaTopicInput() const {
    if (!kafkaTopicInput_.has_value()) {
        throw std::runtime_error("KAFKA_TOPIC_INPUT not configured");
    }
    return kafkaTopicInput_.value();
}
std::string Config::kafkaTopicOutput() const {
    if (!kafkaTopicOutput_.has_value()) {
        throw std::runtime_error("KAFKA_TOPIC_OUTPUT not configured");
    }
    return kafkaTopicOutput_.value();
}

std::string Config::kafkaTopicDLQ() const {
    if (!kafkaTopicDLQ_.has_value()) {
        throw std::runtime_error("KAFKA_TOPIC_DLQ not configured");
    }
    return kafkaTopicDLQ_.value();
}

int Config::maxRetries() const { return maxRetries_; }

std::string Config::s3Host() const {
    if (!s3Host_.has_value()) {
        throw std::runtime_error("S3_HOST not configured");
    }
    return s3Host_.value();
}
std::string Config::s3AccessKey() const {
    if (!s3AccessKey_.has_value()) {
        throw std::runtime_error("S3_ACCESS_KEY not configured");
    }
    return s3AccessKey_.value();
}
std::string Config::s3SecretKey() const {
    if (!s3SecretKey_.has_value()) {
        throw std::runtime_error("S3_SECRET_KEY not configured");
    }
    return s3SecretKey_.value();
}
std::string Config::s3BucketInput() const {
    if (!s3BucketInput_.has_value()) {
        throw std::runtime_error("S3_BUCKET_INPUT not configured");
    }
    return s3BucketInput_.value();
}
std::string Config::s3BucketOutput() const {
    if (!s3BucketOutput_.has_value()) {
        throw std::runtime_error("S3_BUCKET_OUTPUT not configured");
    }
    return s3BucketOutput_.value();
}
Logger::Level Config::logLevel() const { return logLevel_; }
bool Config::logDebug() const { return logDebug_; }
bool Config::preview() const { return preview_; }