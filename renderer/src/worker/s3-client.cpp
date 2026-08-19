#include "s3-client.hpp"

#include <aws/core/Aws.h>
#include <aws/s3/S3ServiceClientModel.h>
#include <aws/s3/model/GetObjectRequest.h>
#include <aws/s3/model/PutObjectRequest.h>

#include <exception>
#include <stdexcept>

#include "logger.hpp"

S3Client::S3Client(const std::string& endpoint, Aws::Auth::AWSCredentials credentials) : logger("S3") {
    try {
        Aws::Client::ClientConfiguration clientConfig;
        clientConfig.endpointOverride = endpoint;
        clientConfig.scheme = Aws::Http::Scheme::HTTP;
        clientConfig.verifySSL = false;

        s3Client = Aws::S3::S3Client(credentials, clientConfig,
                                     Aws::Client::AWSAuthV4Signer::PayloadSigningPolicy::Never, false);
    } catch (const std::exception& e) {
        throw std::runtime_error(std::format("Failed to create S3 client: endpoint = {}", endpoint));
    }
    logger.debug(std::format("Client was created: endpoint = {}", endpoint));
}

std::vector<uint8_t> S3Client::getData(const Aws::String& bucketName, const Aws::String& objectKey) {
    Aws::S3::Model::GetObjectRequest request;
    request.SetBucket(bucketName);
    request.SetKey(objectKey);

    auto outcome = s3Client.GetObject(request);

    if (outcome.IsSuccess()) {
        Aws::IOStream& ioStream = outcome.GetResult().GetBody();
        logger.debug(std::format("Get data from S3 (bucket = '{}', key = '{}')", bucketName, objectKey));
        std::vector<uint8_t> data{std::istreambuf_iterator<char>(ioStream), std::istreambuf_iterator<char>()};

        return data;
    } else {
        logger.error(std::format("Failed to read from S3 (bucket = '{}', key = '{}') : ", bucketName, objectKey,
                                 outcome.GetError().GetMessage()));
        throw std::runtime_error(std::format("Failed to read from S3 (bucket = '{}', key = '{}') : ", bucketName,
                                             objectKey, outcome.GetError().GetMessage()));
    }
}

void S3Client::putData(const std::vector<uint8_t>& data, const Aws::String& bucketName, const Aws::String& objectKey) {
    Aws::S3::Model::PutObjectRequest request;
    request.SetBucket(bucketName);
    request.SetKey(objectKey);
    auto bodyStream = std::make_shared<Aws::StringStream>();
    bodyStream->write(reinterpret_cast<const char*>(data.data()), data.size());
    request.SetBody(bodyStream);

    auto outcome = s3Client.PutObject(request);

    if (outcome.IsSuccess()) {
        logger.debug(std::format("Put data to S3 (bucket = '{}', key = '{}') : ", bucketName, objectKey));

    } else {
        logger.error(std::format("Failed to put data to (bucket = '{}', key = '{}'): {}", bucketName, objectKey,
                                 outcome.GetError().GetMessage()));
        throw std::runtime_error(std::format("Failed to put data to (bucket = '{}', key = '{}'): {}", bucketName,
                                             objectKey, outcome.GetError().GetMessage()));
    }
}

S3Client::~S3Client() {}