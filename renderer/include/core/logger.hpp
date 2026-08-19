#pragma once
#include <string_view>

class Logger {
   public:
    enum class Level { INFO, DEBUG, WARNING, ERROR, FATAL };
    static bool showDebug;

    Logger(std::string_view scope);

    static void setMinLevel(Level level) { minLevel = level; }

    void info(std::string_view message) const;
    void warning(std::string_view message) const;
    void debug(std::string_view message) const;
    void error(std::string_view message) const;
    void fatal(std::string_view message) const;

    static std::string getStringFromLevel(Level level);
    static Level getLevelFromString(const std::string& level);

    ~Logger() = default;

   private:
    static Level minLevel;
    std::string_view scope;

    void log(std::string_view message, Level level) const;
};