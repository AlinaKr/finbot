from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    Numeric,
    Text,
    ForeignKey,
    UniqueConstraint,
    Enum,
    func
)
import enum
import json


class JSONEncoded(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)


DateTimeTz = DateTime(timezone=True)
Base = declarative_base()


class UserAccount(Base):
    __tablename__ = "finbot_users"
    id = Column(Integer, primary_key=True)
    email = Column(String(128), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    full_name = Column(String(128), nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())
    external_accounts = relationship("ExternalAccount", back_populates="user_account")
    settings = relationship("UserAccountSettings", uselist=False, back_populates="user_account")


class UserAccountSettings(Base):
    __tablename__ = "finbot_users_settings"
    user_account_id = Column(Integer, ForeignKey("finbot_users.id"), primary_key=True)
    valuation_ccy = Column(String(3), nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())
    user_account = relationship("UserAccount", uselist=False, back_populates="settings")


class Provider(Base):
    __tablename__ = "finbot_providers"
    id = Column(String(64), primary_key=True)
    description = Column(String(256), nullable=False)
    website_url = Column(String(256), nullable=False)
    credentials_schema = Column(JSONEncoded, nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())


class ExternalAccount(Base):
    __tablename__ = "finbot_external_accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("finbot_users.id"), nullable=False)
    provider_id = Column(String(64), ForeignKey("finbot_providers.id"), nullable=False)
    account_name = Column(String(64), nullable=False)
    encrypted_credentials = Column(Text)
    deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())
    user_account = relationship("UserAccount", uselist=False, back_populates="external_accounts")
    provider = relationship("Provider")
    __table_args__ = (
        UniqueConstraint(
            user_id, provider_id, account_name,
            name="uidx_external_accounts_user_provider_account_name"),
    )


class SnapshotStatus(enum.Enum):
    pending = 1
    processing = 2
    success = 3
    failure = 4


class UserAccountSnapshot(Base):
    __tablename__ = "user_accounts_snapshots"
    id = Column(Integer, primary_key=True)
    status = Column(Enum(SnapshotStatus), nullable=False)
    requested_ccy = Column(String(3), nullable=False)
    start_time = Column(DateTimeTz)
    end_time = Column(DateTimeTz)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())
    xccy_rates_entries = relationship("XccyRateSnapshotEntry", back_populates="snapshot")
    external_accounts_entries = relationship("ExternalAccountSnapshotEntry", back_populates="snapshot")


class XccyRateSnapshotEntry(Base):
    __tablename__ = "finbot_xccy_rates_snapshots"
    snapshot_id = Column(Integer, ForeignKey("user_accounts_snapshots.id"), primary_key=True)
    xccy_pair = Column(String(6), primary_key=True)
    rate = Column(Numeric, nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())
    snapshot = relationship("UserAccountSnapshot", uselist=False, back_populates="xccy_rates_entries")


class ExternalAccountSnapshotEntry(Base):
    __tablename__ = "finbot_external_accounts_snapshots"
    entry_id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey("user_accounts_snapshots.id"))
    external_account_id = Column(Integer, ForeignKey("finbot_external_accounts.id"))
    hist_provider_name = Column(String(32), nullable=False)
    hist_provider_description = Column(String(256), nullable=False)
    hist_account_name = Column(String(64), nullable=False)
    value_snapshot_ccy = Column(Numeric, nullable=False)
    overall_weight = Column(Numeric, nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())
    snapshot = relationship("UserAccountSnapshot", uselist=False, back_populates="external_accounts_entries")


class UserAccountDailyValuationEntry(Base):
    __tablename__ = "finbot_user_accounts_daily_valuations"
    entry_id = Column(Integer, primary_key=True)
    user_account_id = Column(Integer, ForeignKey("finbot_users.id"))
    valuation_ccy = Column(String(3), nullable=False)
    valuation_date = Column(Date, nullable=False)
    min_value = Column(Numeric, nullable=False)
    max_value = Column(Numeric, nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())
    user_account = relationship("UserAccount", uselist=False)