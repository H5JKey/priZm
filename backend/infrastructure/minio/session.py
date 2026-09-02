from aiobotocore import session
from aiobotocore.session import AioSession

S3_SESSION = session.get_session()


def get_minio_session() -> AioSession:
    return S3_SESSION
