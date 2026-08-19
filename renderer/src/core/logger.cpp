#include "logger.hpp"

#include <chrono>
#include <format>
#include <iostream>
#include <stdexcept>

bool Logger::showDebug = false;
Logger::Level Logger::minLevel = Logger::Level::INFO;

Logger::Logger(std::string_view scope) : scope(scope) {}

void Logger::log(std::string_view message, Logger::Level level) const {
    if (level == Level::DEBUG && showDebug == false) return;
    if (level < minLevel) return;
    std::clog << std ::format("[{:%Y-%m-%d %H:%M:%S}] [{}] [{}] {}",
                              std::chrono::floor<std::chrono::seconds>(std::chrono::system_clock::now()), scope,
                              getStringFromLevel(level), message)
              << std::endl;
}

void Logger::info(std::string_view message) const { log(message, Logger::Level::INFO); }
void Logger::warning(std::string_view message) const { log(message, Logger::Level::WARNING); }
void Logger::debug(std::string_view message) const { log(message, Logger::Level::DEBUG); }
void Logger::error(std::string_view message) const { log(message, Logger::Level::ERROR); }
void Logger::fatal(std::string_view message) const { log(message, Logger::Level::FATAL); }

std::string Logger::getStringFromLevel(Logger::Level level) {
    switch (level) {
        case Logger::Level::INFO:
            return "INFO";
        case Logger::Level::WARNING:
            return "WARN";
        case Logger::Level::ERROR:
            return "ERROR";
        case Logger::Level::FATAL:
            return "FATAL";
        case Logger::Level::DEBUG:
            return "DEBUG";
    }
    throw std::invalid_argument("Invalid log level");
}

Logger::Level Logger::getLevelFromString(const std::string& level) {
    if (level == "INFO") return Logger::Level::INFO;
    if (level == "WARNING" || level == "WARN") return Logger::Level::WARNING;
    if (level == "ERROR") return Logger::Level::ERROR;
    if (level == "DEBUG") return Logger::Level::DEBUG;
    if (level == "FATAL") return Logger::Level::FATAL;
    throw std::invalid_argument(std::format("Invalid log level: {}", level));
}