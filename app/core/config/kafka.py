from pydantic import BaseModel


class KafkaTopicConfig(BaseModel):
    create_project: str = "create_project"
    generate_render: str = "generate_model"


class KafkaConfig(BaseModel):
    host: str = "kafka"
    port: int = 9092

    topic: KafkaTopicConfig = KafkaTopicConfig()
