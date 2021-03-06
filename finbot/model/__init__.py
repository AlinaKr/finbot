from finbot.core.dbutils import JSONEncoded, DateTimeTz
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Numeric,
    Text,
    ForeignKey,
    ForeignKeyConstraint,
    UniqueConstraint,
    Enum,
    func
)
import enum


Base = declarative_base()


class UserAccount(Base):
    __tablename__ = "finbot_user_accounts"
    id = Column(Integer, primary_key=True)
    email = Column(String(128), nullable=False, unique=True)
    encrypted_password = Column(Text, nullable=False)
    full_name = Column(String(128), nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())
    
    linked_accounts = relationship("LinkedAccount", back_populates="user_account")
    settings = relationship(
        "UserAccountSettings", 
        uselist=False, 
        back_populates="user_account")


class UserAccountSettings(Base):
    __tablename__ = "finbot_user_accounts_settings"
    user_account_id = Column(Integer, ForeignKey(UserAccount.id, ondelete='CASCADE'), primary_key=True)
    valuation_ccy = Column(String(3), nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    user_account = relationship(UserAccount, uselist=False, back_populates="settings")


class Provider(Base):
    __tablename__ = "finbot_providers"
    id = Column(String(64), primary_key=True)
    description = Column(String(256), nullable=False)
    website_url = Column(String(256), nullable=False)
    credentials_schema = Column(JSONEncoded, nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    def serialize(self):
        return {
            "id": self.id,
            "description": self.description,
            "website_url": self.website_url,
            "credentials_schema": self.credentials_schema,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class LinkedAccount(Base):
    __tablename__ = "finbot_linked_accounts"
    id = Column(Integer, primary_key=True)
    user_account_id = Column(Integer, ForeignKey(UserAccount.id, ondelete="CASCADE"), nullable=False)
    provider_id = Column(String(64), ForeignKey(Provider.id, ondelete="CASCADE"), nullable=False)
    account_name = Column(String(64), nullable=False)
    encrypted_credentials = Column(Text)
    deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    user_account = relationship(
        UserAccount, 
        uselist=False, 
        back_populates="linked_accounts")
    
    provider = relationship("Provider", uselist=False)

    __table_args__ = (
        UniqueConstraint(
            user_account_id, provider_id, account_name,
            name="uidx_linked_accounts_user_provider_account_name"),
    )


class SnapshotStatus(enum.Enum):
    Pending = 1
    Processing = 2
    Success = 3
    Failure = 4


class UserAccountSnapshot(Base):
    __tablename__ = "finbot_user_accounts_snapshots"
    id = Column(Integer, primary_key=True)
    user_account_id = Column(Integer, ForeignKey(UserAccount.id, ondelete='CASCADE'), nullable=False)
    status = Column(Enum(SnapshotStatus), nullable=False)
    requested_ccy = Column(String(3), nullable=False)
    start_time = Column(DateTimeTz, index=True)
    end_time = Column(DateTimeTz, index=True)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    user_account = relationship(UserAccount, uselist=False)
    xccy_rates_entries = relationship(
        "XccyRateSnapshotEntry", 
        back_populates="snapshot")
    linked_accounts_entries = relationship(
        "LinkedAccountSnapshotEntry", 
        back_populates="snapshot")

    @property
    def effective_at(self):
        return self.end_time


class XccyRateSnapshotEntry(Base):
    __tablename__ = "finbot_xccy_rates_snapshots"
    snapshot_id = Column(Integer, ForeignKey(UserAccountSnapshot.id, ondelete="CASCADE"), primary_key=True)
    xccy_pair = Column(String(6), primary_key=True)
    rate = Column(Numeric, nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    snapshot = relationship(
        UserAccountSnapshot, 
        uselist=False, 
        back_populates="xccy_rates_entries")


class LinkedAccountSnapshotEntry(Base):
    __tablename__ = "finbot_linked_accounts_snapshots"
    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey(UserAccountSnapshot.id, ondelete="CASCADE"))
    linked_account_id = Column(Integer, ForeignKey("finbot_linked_accounts.id", ondelete="CASCADE"))
    success = Column(Boolean, nullable=False)
    failure_details = Column(JSONEncoded)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    snapshot = relationship(
        UserAccountSnapshot, 
        uselist=False, 
        back_populates="linked_accounts_entries")
    sub_accounts_entries = relationship(
        "SubAccountSnapshotEntry", 
        back_populates="linked_account_entry")


class SubAccountSnapshotEntry(Base):
    __tablename__ = "finbot_sub_accounts_snapshot_entries"
    id = Column(Integer, primary_key=True)
    linked_account_snapshot_entry_id = Column(Integer, ForeignKey(LinkedAccountSnapshotEntry.id, ondelete="CASCADE"))
    sub_account_id = Column(String(32), nullable=False)
    sub_account_ccy = Column(String(3), nullable=False)
    sub_account_description = Column(String(256), nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    linked_account_entry = relationship(
        LinkedAccountSnapshotEntry, 
        uselist=False, 
        back_populates="sub_accounts_entries")
    items_entries = relationship(
        "SubAccountItemSnapshotEntry", 
        back_populates="sub_account_entry")


class SubAccountItemType(enum.Enum):
    Asset = 1
    Liability = 2


class SubAccountItemSnapshotEntry(Base):
    __tablename__ = "finbot_sub_accounts_items_snapshot_entries"
    id = Column(Integer, primary_key=True)
    sub_account_snapshot_entry_id = Column(Integer, ForeignKey(SubAccountSnapshotEntry.id, ondelete="CASCADE"), nullable=False)
    item_type = Column(Enum(SubAccountItemType), nullable=False)
    name = Column(String(256), nullable=False)
    item_subtype = Column(String(32), nullable=False)
    units = Column(Numeric)
    value_sub_account_ccy = Column(Numeric)
    value_snapshot_ccy = Column(Numeric)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    sub_account_entry = relationship(
        SubAccountSnapshotEntry, 
        uselist=False, 
        back_populates="items_entries")


class ValuationChangeEntry(Base):
    __tablename__ = "finbot_valuation_change_entries"
    id = Column(Integer, primary_key=True)
    change_1hour = Column(Numeric)
    change_1day = Column(Numeric)
    change_1week = Column(Numeric)
    change_1month = Column(Numeric)
    change_6months = Column(Numeric)
    change_1year = Column(Numeric)
    change_2years = Column(Numeric)

    def serialize(self):
        return {
            "change_1hour": self.change_1hour,
            "change_1day": self.change_1day,
            "change_1week": self.change_1week,
            "change_1month": self.change_1month,
            "change_6months": self.change_6months,
            "change_1year": self.change_1year,
            "change_2years": self.change_2years,
        }


class UserAccountHistoryEntry(Base):
    __tablename__ = "finbot_user_accounts_history_entries"
    id = Column(Integer, primary_key=True)
    user_account_id = Column(Integer, ForeignKey(UserAccount.id, ondelete="CASCADE"), nullable=False)
    source_snapshot_id = Column(Integer, ForeignKey(UserAccountSnapshot.id, ondelete="SET NULL"))
    valuation_ccy = Column(String(3), nullable=False)
    effective_at = Column(DateTimeTz, nullable=False, index=True)
    available = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    user_account = relationship(UserAccount, uselist=False)
    source_snapshot = relationship(UserAccountSnapshot, uselist=False)
    user_account_valuation_history_entry = relationship(
        "UserAccountValuationHistoryEntry", 
        uselist=False, 
        back_populates="account_valuation_history_entry")
    linked_accounts_valuation_history_entries = relationship(
        "LinkedAccountValuationHistoryEntry", 
        back_populates="account_valuation_history_entry")
    sub_accounts_valuation_history_entries = relationship(
        "SubAccountValuationHistoryEntry", 
        back_populates="account_valuation_history_entry")
    sub_accounts_items_valuation_history_entries = relationship(
        "SubAccountItemValuationHistoryEntry", 
        back_populates="account_valuation_history_entry")


class UserAccountValuationHistoryEntry(Base):
    __tablename__ = "finbot_user_accounts_valuation_history_entries"
    history_entry_id = Column(Integer, ForeignKey(UserAccountHistoryEntry.id, ondelete="CASCADE"), primary_key=True)
    valuation = Column(Numeric, nullable=False)
    total_liabilities = Column(Numeric, nullable=False, server_default="0.0")
    valuation_change_id = Column(Integer, ForeignKey(ValuationChangeEntry.id, ondelete="SET NULL"))
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    valuation_change = relationship(ValuationChangeEntry, uselist=False)
    account_valuation_history_entry = relationship(
        UserAccountHistoryEntry,
        uselist=False,
        back_populates="user_account_valuation_history_entry")

    @property
    def total_assets(self):
        return self.valuation - self.total_liabilities


class LinkedAccountValuationHistoryEntry(Base):
    __tablename__ = "finbot_linked_accounts_valuation_history_entries"
    history_entry_id = Column(Integer, ForeignKey(UserAccountHistoryEntry.id, ondelete="CASCADE"), primary_key=True)
    linked_account_id = Column(Integer, ForeignKey(LinkedAccount.id, ondelete="CASCADE"), primary_key=True)
    effective_snapshot_id = Column(Integer, ForeignKey(UserAccountSnapshot.id, ondelete="SET NULL"))
    valuation = Column(Numeric, nullable=False)
    total_liabilities = Column(Numeric, nullable=False, server_default="0.0")
    valuation_change_id = Column(Integer, ForeignKey(ValuationChangeEntry.id, ondelete="SET NULL"))
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    effective_snapshot = relationship(UserAccountSnapshot, uselist=False)
    valuation_change = relationship(ValuationChangeEntry, uselist=False)
    linked_account = relationship(LinkedAccount, uselist=False)
    account_valuation_history_entry = relationship(
        UserAccountHistoryEntry,
        uselist=False,
        back_populates="linked_accounts_valuation_history_entries")

    @property
    def total_assets(self):
        return self.valuation - self.total_liabilities


class SubAccountValuationHistoryEntry(Base):
    __tablename__ = "finbot_sub_accounts_valuation_history_entries"
    history_entry_id = Column(Integer, ForeignKey(UserAccountHistoryEntry.id, ondelete="CASCADE"), primary_key=True)
    linked_account_id = Column(Integer, ForeignKey(LinkedAccount.id, ondelete="CASCADE"), primary_key=True)
    sub_account_id = Column(String(32), primary_key=True)
    sub_account_ccy = Column(String(3), nullable=False)
    sub_account_description = Column(String(256), nullable=False)
    valuation = Column(Numeric, nullable=False)
    total_liabilities = Column(Numeric, nullable=False, server_default="0.0")
    valuation_sub_account_ccy = Column(Numeric, nullable=False)
    valuation_change_id = Column(Integer, ForeignKey(ValuationChangeEntry.id, ondelete="SET NULL"))
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    valuation_change = relationship(ValuationChangeEntry, uselist=False)
    linked_account = relationship(LinkedAccount, uselist=False)
    account_valuation_history_entry = relationship(
        UserAccountHistoryEntry,
        uselist=False,
        back_populates="sub_accounts_valuation_history_entries")
    sub_accounts_items_valuation_history_entries = relationship(
        "SubAccountItemValuationHistoryEntry",
        back_populates="sub_account_valuation_history_entry")

    @property
    def total_assets(self):
        return self.valuation - self.total_liabilities


class SubAccountItemValuationHistoryEntry(Base):
    __tablename__ = "finbot_sub_accounts_items_valuation_history_entries"
    history_entry_id = Column(Integer, ForeignKey(UserAccountHistoryEntry.id, ondelete="CASCADE"), primary_key=True)
    linked_account_id = Column(Integer, ForeignKey(LinkedAccount.id, ondelete="CASCADE"), primary_key=True)
    sub_account_id = Column(String(32), primary_key=True)
    item_type = Column(Enum(SubAccountItemType), primary_key=True)
    name = Column(String(256), primary_key=True)
    item_subtype = Column(String(32), nullable=False)
    units = Column(Numeric)
    valuation = Column(Numeric, nullable=False)
    valuation_sub_account_ccy = Column(Numeric, nullable=False)
    valuation_change_id = Column(Integer, ForeignKey(ValuationChangeEntry.id, ondelete="SET NULL"))
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    valuation_change = relationship(ValuationChangeEntry, uselist=False)
    linked_account = relationship(LinkedAccount, uselist=False)
    account_valuation_history_entry = relationship(
        UserAccountHistoryEntry,
        uselist=False,
        back_populates="sub_accounts_items_valuation_history_entries")
    sub_account_valuation_history_entry = relationship(
        SubAccountValuationHistoryEntry,
        uselist=False,
        back_populates="sub_accounts_items_valuation_history_entries",
        viewonly=True,
        foreign_keys=[
            history_entry_id, 
            linked_account_id, 
            sub_account_id
        ]
    )

    __table_args__ = (
        ForeignKeyConstraint(
            [
                history_entry_id, 
                linked_account_id, 
                sub_account_id
            ],
            [
                SubAccountValuationHistoryEntry.history_entry_id,
                SubAccountValuationHistoryEntry.linked_account_id,
                SubAccountValuationHistoryEntry.sub_account_id
            ]
        ),
    )
