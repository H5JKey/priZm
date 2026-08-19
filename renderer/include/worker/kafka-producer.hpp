#pragma once
#include <cppkafka.h>

#include <string>

#include "logger.hpp"
#include "producer.h"

class KafkaProducer {
    Logger logger;
    std::string brokerList;
    cppkafka::Configuration config;

    cppkafka::Producer producer;

   public:
    KafkaProducer(const std::string& brokerList);
    void produce(const std::string& topicName, const std::string& strMessage);
    ~KafkaProducer();
};