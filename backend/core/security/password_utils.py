from bcrypt import checkpw, gensalt, hashpw
from schemas.auth import RegisterRequest
from schemas.user import UserCreate


def hash_password(password: str) -> str:
    salt = gensalt()
    password_bytes = password.encode()
    hashed_password_bytes = hashpw(
        password=password_bytes,
        salt=salt,
    )
    hashed_password = hashed_password_bytes.decode()
    return hashed_password


def validate_password(
    password: str,
    encrypted_password: str,
) -> bool:
    password_bytes = password.encode()
    hashed_password_bytes = encrypted_password.encode()
    return checkpw(
        password=password_bytes,
        hashed_password=hashed_password_bytes,
    )


def convert_register_to_create_user(register_user_data: RegisterRequest) -> UserCreate:
    password = register_user_data.password
    encrypted_password = hash_password(password)
    register_user_data_dict = register_user_data.model_dump(
        exclude={"password"},
    )
    create_user_data = UserCreate(
        encrypted_password=encrypted_password,
        **register_user_data_dict,
    )
    return create_user_data
