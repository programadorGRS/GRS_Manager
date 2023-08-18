from flask_limiter.util import get_remote_address
from sqlalchemy import text

from src.extensions import database as db


class ClientIP(db.Model):
    """Configuração para rate limiting por IP"""

    __tablename__ = "ClientIP"

    id = db.Column(db.Integer, primary_key=True)
    ip_addr = db.Column(db.String(255), nullable=False, unique=True)
    rate_limit = db.Column(db.Boolean, nullable=False, server_default=text("0"))

    @classmethod
    def is_rate_limit_exempt(cls) -> bool:
        """
        Returns True if current client's IP address is free of rate
        limiting else returns  False
        """
        ip_addr = get_remote_address()
        client: cls | None = (
            db.session.query(cls).filter(cls.ip_addr == ip_addr).first()
        )

        if not client:
            return False

        return not bool(client.rate_limit)
