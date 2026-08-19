#include "denoiser.hpp"

#include <stdexcept>

#include "logger.hpp"
#include "utils.hpp"

Denoiser::Denoiser() {
    device = oidn::newDevice(oidn::DeviceType::CPU);
    device.commit();
}

void Denoiser::denoise(RenderTarget& target) {
    int pixelCount = target.getWidth() * target.getHeight();
    size_t bufferSize = pixelCount * 3 * sizeof(float);

    std::vector<float> colorBufferData(pixelCount * 3, 0.0f);
    utils::rgbaToRgb(target.getBufferData<float>(target.getRawTexture()), colorBufferData);
    oidn::BufferRef colorBuffer = device.newBuffer(colorBufferData.data(), bufferSize);

    std::vector<float> normalBufferData(pixelCount * 3, 0.0f);
    utils::rgbaToRgb(target.getBufferData<float>(target.getNormalMap()), normalBufferData);
    oidn::BufferRef normalBuffer = device.newBuffer(normalBufferData.data(), bufferSize);

    std::vector<float> albedoBufferData(pixelCount * 3, 0.0f);
    utils::rgbaToRgb(target.getBufferData<float>(target.getAlbedoMap()), albedoBufferData);
    oidn::BufferRef albedoBuffer = device.newBuffer(albedoBufferData.data(), bufferSize);

    std::vector<float> resultBufferData(pixelCount * 3, 0.0f);
    oidn::BufferRef outputBuffer = device.newBuffer(resultBufferData.data(), bufferSize);

    oidn::FilterRef filter = device.newFilter("RT");
    filter.setImage("color", colorBuffer, oidn::Format::Float3, target.getWidth(), target.getHeight());
    filter.setImage("normal", normalBuffer, oidn::Format::Float3, target.getWidth(), target.getHeight());
    filter.setImage("albedo", albedoBuffer, oidn::Format::Float3, target.getWidth(), target.getHeight());
    filter.setImage("output", outputBuffer, oidn::Format::Float3, target.getWidth(), target.getHeight());
    filter.set("hdr", true);
    filter.commit();
    filter.execute();

    const char* errorMessage;
    if (device.getError(errorMessage) != oidn::Error::None) {
        throw std::runtime_error(errorMessage);
    }

    std::vector<float> denoisedImageData(pixelCount * 4, 0);
    utils::rgbToRgba(resultBufferData, denoisedImageData);
    target.setBufferData(target.getDenoisedTexture(), denoisedImageData);
}