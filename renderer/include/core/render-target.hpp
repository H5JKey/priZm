#pragma once

#define EGL_EGLEXT_PROTOTYPES
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <glad/gl.h>

#include <stdexcept>
#include <vector>

#include "logger.hpp"

class TargetManager;

class RenderTarget {
    friend class ContextGuard;

   protected:
    friend class TargetManager;
    int width, height;
    bool initialized = false;
    GLuint rawTexture;
    GLuint denoisedTexture;
    GLuint outputTexture;
    GLuint normalMap;
    GLuint albedoMap;

    RenderTarget(int width, int height) : width{width}, height{height} {}
    virtual void makeCurrent() const = 0;
    virtual void release() const = 0;

   public:
    int getWidth() const noexcept { return width; }
    int getHeight() const noexcept { return height; }
    GLuint getRawTexture() const noexcept { return rawTexture; }
    GLuint getDenoisedTexture() const noexcept { return denoisedTexture; }
    GLuint getOutputTexture() const noexcept { return outputTexture; }
    GLuint getNormalMap() const noexcept { return normalMap; }
    GLuint getAlbedoMap() const noexcept { return albedoMap; }

    template <typename T>
        requires std::is_same_v<T, uint8_t> || std::is_same_v<T, float>
    std::vector<T> getBufferData(GLuint texture) const;

    template <typename T>
        requires std::is_same_v<T, uint8_t> || std::is_same_v<T, float>
    void setBufferData(GLuint texture, const std::vector<T>& pixels);

    virtual ~RenderTarget() = default;
};

class EglTarget : public RenderTarget {
    friend class TargetManager;
    EglTarget(int width, int height, EGLDisplay display, EGLConfig config, EGLContext context);

    void makeCurrent() const override;
    void release() const override;
    EGLDisplay display;
    EGLSurface surface;
    EGLContext context;
    Logger logger;

   public:
    ~EglTarget();
};

#include "render-target.inl"
