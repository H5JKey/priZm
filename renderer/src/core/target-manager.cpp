#include "target-manager.hpp"

#include <format>
#include <stdexcept>

#include "logger.hpp"

TargetManager& TargetManager::getInstance() {
    static TargetManager instance;
    return instance;
}

TargetManager::TargetManager() : logger("EGL") {}

void TargetManager::init() {
    TargetManager& self = getInstance();
    if (!self.initialized) {
        self.logger.debug("Initializing EGL");
        self.display = eglGetPlatformDisplay(EGL_PLATFORM_SURFACELESS_MESA, EGL_DEFAULT_DISPLAY, nullptr);
        if (self.display == EGL_NO_DISPLAY) {
            self.logger.fatal("Failed to get display");
            throw std::runtime_error("Failed to get display");
        }

        if (!eglInitialize(self.display, &self.majorVersion, &self.minorVersion)) {
            self.logger.fatal("Failed to initialize EGL");
            throw std::runtime_error("Failed to initialize EGL");
        }

        eglBindAPI(EGL_OPENGL_API);

        EGLint configAttribs[] = {EGL_SURFACE_TYPE,
                                  EGL_PBUFFER_BIT,
                                  EGL_RENDERABLE_TYPE,
                                  EGL_OPENGL_BIT,
                                  EGL_RED_SIZE,
                                  8,
                                  EGL_GREEN_SIZE,
                                  8,
                                  EGL_BLUE_SIZE,
                                  8,
                                  EGL_ALPHA_SIZE,
                                  8,
                                  EGL_NONE};

        EGLint numConfigs;
        if (!eglChooseConfig(self.display, configAttribs, &self.config, 1, &numConfigs)) {
            self.logger.fatal("Failed to choose config");
            throw std::runtime_error("Failed to choose config");
        }

        EGLint contextAttribs[] = {
            EGL_CONTEXT_MAJOR_VERSION,           4,       EGL_CONTEXT_MINOR_VERSION, 3, EGL_CONTEXT_OPENGL_PROFILE_MASK,
            EGL_CONTEXT_OPENGL_CORE_PROFILE_BIT, EGL_NONE};

        if (!(self.context = eglCreateContext(self.display, self.config, EGL_NO_CONTEXT, contextAttribs))) {
            EGLint error = eglGetError();
            self.logger.fatal("Failed to create EGL context. Error: " + std::to_string(error));
            throw std::runtime_error("Failed to create EGL context. Error: " + std::to_string(error));
        }

        EGLint surfaceAttribs[] = {EGL_WIDTH, 1, EGL_HEIGHT, 1, EGL_NONE};
        if (!(self.dummySurface = eglCreatePbufferSurface(self.display, self.config, surfaceAttribs))) {
            self.logger.fatal("Failed to initialize EGL surface");
            throw std::runtime_error("Failed to initialize EGL surface");
        }

        if (!eglMakeCurrent(self.display, self.dummySurface, self.dummySurface, self.context)) {
            self.logger.fatal("eglMakeCurrent for dummy surface in TargetManager::init failed");
            throw std::runtime_error("eglMakeCurrent for dummy surface in TargetManager::init failed");
        }

        if (!gladLoadGL(eglGetProcAddress)) {
            self.logger.fatal("gladLoadGL failed");
            throw std::runtime_error("gladLoadGL failed");
        }
        self.logger.debug(std::format("OpenGL info:\n\tVendor   :  {}\n\tRenderer :  {}\n\tVersion  :  {}",
                                      (const char*)glGetString(GL_VENDOR), (const char*)glGetString(GL_RENDERER),
                                      (const char*)glGetString(GL_VERSION)));

        self.initialized = true;
    }
}

void TargetManager::terminate() {
    TargetManager& self = getInstance();
    if (self.initialized) {
        eglMakeCurrent(self.display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);

        if (self.dummySurface != EGL_NO_SURFACE) {
            eglDestroySurface(self.display, self.dummySurface);
            self.dummySurface = EGL_NO_SURFACE;
        }

        if (self.context != EGL_NO_CONTEXT) {
            eglDestroyContext(self.display, self.context);
            self.context = EGL_NO_CONTEXT;
        }

        if (self.display != EGL_NO_DISPLAY) {
            eglTerminate(self.display);
            self.display = EGL_NO_DISPLAY;
        }

        self.initialized = false;
        self.logger.debug("EGL Terminated");
    }
}

std::shared_ptr<RenderTarget> TargetManager::createEGLTarget(int width, int height) {
    if (!initialized) {
        logger.error("Failed to create EGLTarget: context wasnt created");
        throw std::runtime_error("Failed to create EGLTarget: context wasnt created");
    }
    return std::shared_ptr<EglTarget>(new EglTarget(width, height, display, config, context));
}

TargetManager::~TargetManager() { terminate(); }
