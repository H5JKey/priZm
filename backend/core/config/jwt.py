from pathlib import Path

from pydantic import BaseModel


class JWTConfig(BaseModel):
    base_dir: Path = Path(__file__).parent.parent.parent
    access_token_expires_in_minutes: int = 15
    refresh_token_expires_in_minutes: int = 30 * 24 * 60
    algorithm: str = "RS256"

    public_key_path: Path = base_dir / "certs" / "jwt-public.pem"
    private_key_path: Path = base_dir / "certs" / "jwt-private.pem"
