add_library(renderer_core STATIC
    scene.cpp
    scene-loader.cpp
    render-engine.cpp
    render-target.cpp
    target-manager.cpp
    denoiser.cpp
    bvh.cpp
    bvh-builder.cpp
    utils.cpp
    stb-implementation.cpp
    logger.cpp
    context-guard.cpp
)

target_link_libraries(renderer_core PUBLIC
    renderer_core_deps
)

target_include_directories(renderer_core PUBLIC
    ${CMAKE_SOURCE_DIR}/include/core
)

add_custom_command(
    TARGET renderer_core POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E create_symlink
        ${CMAKE_SOURCE_DIR}/shaders
        ${CMAKE_BINARY_DIR}/shaders
    COMMENT "Symlinking shaders to build directory"
)