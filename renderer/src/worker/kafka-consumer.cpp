#include "kafka-consumer.hpp"

#include "consumer.h"
#include "logger.hpp"

KafkaConsumer::KafkaConsumer(const std::string& brokerList, const std::string& groupId, const std::string& topicName)
    : logger("KAFKA"),
      topicName(topicName),
      brokerList(brokerList),
      groupId(groupId),
      config({
          {"metadata.broker.list", this->brokerList},
          {"group.id", this->groupId},
          {"auto.offset.reset", "earliest"},
          {"broker.address.family", "v4"},
          {"enable.auto.commit", "false"},
          {"auto.commit.interval.ms", "0"},
      }),
      consumer(config) {
    try {
        consumer.subscribe({std::string(topicName)});
        logger.debug(std::format("Consuming messages from topic '{}'", topicName));
    } catch (const std::exception& e) {
        logger.fatal(std::format("Failed to subscribe topic '{}'", topicName));
        throw;
    }
}

KafkaConsumer::~KafkaConsumer() { consumer.unsubscribe(); }

std::string KafkaConsumer::consume() {
    while (true) {
        auto message = consumer.poll(std::chrono::milliseconds(10000));
        if (message) {
            if (message.get_error()) {
                logger.error(std::format("Error: {}", message.get_error().to_string()));
            } else {
                std::string strMessage(reinterpret_cast<const char*>(message.get_payload().get_data()),
                                       message.get_payload().get_size());
                logger.debug(std::format("Kafka consumed message ({}, offset = {}, partition = {})", strMessage,
                                         message.get_offset(), message.get_partition()));
                lastMessage = std::move(message);
                return strMessage;
            }
        }
    }
}

void KafkaConsumer::commit() {
    if (lastMessage.has_value()) {
        logger.debug(std::format("Commit message (offset: {}, partition: {})", lastMessage.value().get_offset(),
                                 lastMessage.value().get_partition()));
        consumer.commit(lastMessage.value());
    } else {
        logger.warning("Nothing was committed. There have been no messages yet");
    }
}