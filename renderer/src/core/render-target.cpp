#include "render-target.hpp"

#include <format>
#include <stdexcept>

#include "context-guard.hpp"

EglTarget::EglTarget(int width, int height, EGLDisplay display, EGLConfig config, EGLContext context)
    : RenderTarget(width, height), display(display), context(context), logger("EGL") {
    EGLint surfaceAttribs[] = {EGL_WIDTH, width, EGL_HEIGHT, height, EGL_NONE};
    if (!(surface = eglCreatePbufferSurface(display, config, surfaceAttribs))) {
        logger.error("Failed to initialize surface");
        throw std::runtime_error("Failed to initialize EGL surface");
    }
    {
        ContextGuard context(*this);
        glGenTextures(1, &rawTexture);
        glBindTexture(GL_TEXTURE_2D, rawTexture);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, nullptr);
        glBindTexture(GL_TEXTURE_2D, 0);

        glGenTextures(1, &denoisedTexture);
        glBindTexture(GL_TEXTURE_2D, denoisedTexture);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, nullptr);
        glBindTexture(GL_TEXTURE_2D, 0);

        glGenTextures(1, &normalMap);
        glBindTexture(GL_TEXTURE_2D, normalMap);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, nullptr);
        glBindTexture(GL_TEXTURE_2D, 0);

        glGenTextures(1, &albedoMap);
        glBindTexture(GL_TEXTURE_2D, albedoMap);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, nullptr);
        glBindTexture(GL_TEXTURE_2D, 0);

        glGenTextures(1, &outputTexture);
        glBindTexture(GL_TEXTURE_2D, outputTexture);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
        glBindTexture(GL_TEXTURE_2D, 0);
    }
    initialized = true;
    logger.debug(std::format("EGl target created ({}x{})", width, height));
}

void EglTarget::makeCurrent() const {
    eglMakeCurrent(display, surface, surface, context);
    EGLint error = eglGetError();
    if (error != EGL_SUCCESS) {
        logger.error(std::format("eglMakeCurrent in EglTarget::makeCurrent failed. Error: {}", error));
        throw std::runtime_error(std::format("eglMakeCurrent in EglTarget::makeCurrent failed. Error: {}", error));
    }
}

void EglTarget::release() const {
    eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    EGLint error = eglGetError();
    if (error != EGL_SUCCESS) {
        logger.error(std::format("eglMakeCurrent in EglTarget::release failed. Error: {}", error));
        throw std::runtime_error(std::format("eglMakeCurrent in EglTarget::release failed. Error: {}", error));
    }
}

EglTarget::~EglTarget() {
    if (initialized) {
        ContextGuard guard(*this);
        glDeleteTextures(1, &denoisedTexture);
        glDeleteTextures(1, &outputTexture);
        glDeleteTextures(1, &rawTexture);
        glDeleteTextures(1, &normalMap);
        glDeleteTextures(1, &albedoMap);
    }
}