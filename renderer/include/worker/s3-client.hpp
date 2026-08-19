#include <aws/core/Aws.h>
#include <aws/core/auth/AWSCredentials.h>
#include <aws/s3/S3Client.h>

#include <string_view>
#include <vector>

#include "logger.hpp"

class S3Client {
    Logger logger;
    Aws::S3::S3Client s3Client;

   public:
    S3Client(const std::string& endpoint, Aws::Auth::AWSCredentials credentials);

    std::vector<uint8_t> getData(const Aws::String& bucketName, const Aws::String& objectKey);
    void putData(const std::vector<uint8_t>& data, const Aws::String& bucketName, const Aws::String& objectKey);
    ~S3Client();
};
