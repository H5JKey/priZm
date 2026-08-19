message(STATUS "Building tests")

include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.17.0
)
FetchContent_MakeAvailable(googletest)

enable_testing()

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/tests)
add_executable(test
    utils/test-rgb-rgba.cpp
    utils/test-imageReadWrite.cpp
    utils/test-readFromFile.cpp
    bvh/test-building.cpp
    bvh/test-intersections.cpp
    scene-loader/test-scene-loader.cpp
    renderer-pipeline/test-renderer-pipeline.cpp
    test-main.cpp
)

target_compile_options(test PRIVATE 
    -O0
    -g
    -fno-omit-frame-pointer
    -fno-inline
    -fno-optimize-sibling-calls
    -fsanitize=address
)

target_link_options(test PRIVATE
    -fsanitize=address
)

target_link_libraries(test PRIVATE
    renderer_core
    GTest::gtest_main
)

add_custom_command(
    TARGET test POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E create_symlink
        ${CMAKE_SOURCE_DIR}/tests/data
        ${CMAKE_BINARY_DIR}/tests/data
    COMMENT "Symlinking tests data to build directory"
)

add_custom_command(
    TARGET test POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E create_symlink
        ${CMAKE_SOURCE_DIR}/tests/asan.supp
        ${CMAKE_BINARY_DIR}/tests/asan.supp
    COMMENT "Symlinking ASan suppression file to build directory"
)


include(GoogleTest)
gtest_discover_tests(test
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
    PROPERTIES
    ENVIRONMENT "TBB_ENABLE_SANITIZERS=1;LSAN_OPTIONS=detect_leaks=1:suppressions=asan.supp"
)