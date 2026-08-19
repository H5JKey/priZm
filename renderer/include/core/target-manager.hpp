#pragma once
#include <memory>

#include "render-target.hpp"

class TargetManager {
   public:
    TargetManager(const TargetManager&) = delete;
    TargetManager(TargetManager&&) = delete;

    TargetManager& operator=(const TargetManager&) = delete;
    TargetManager& operator=(TargetManager&&) = delete;

    static TargetManager& getInstance();
    std::shared_ptr<RenderTarget> createEGLTarget(int width, int height);

    static void init();
    static void terminate();

    EGLDisplay getDisplay() const noexcept { return display; }
    EGLDisplay getContext() const noexcept { return context; }

   private:
    TargetManager();
    ~TargetManager();

   private:
    Logger logger;
    EGLint majorVersion, minorVersion;
    EGLDisplay display;
    EGLConfig config;
    EGLContext context;
    EGLSurface dummySurface;

    bool initialized = false;
};