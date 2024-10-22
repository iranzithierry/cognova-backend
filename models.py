# from sqlalchemy import (
#     String, TIMESTAMP, Integer, JSON, Text, ForeignKey, ARRAY, Boolean, Double, Enum, Index, text, DECIMAL
# )
# from sqlalchemy.orm import relationship, Mapped, mapped_column
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.dialects.postgresql import VECTOR
# from enum import Enum

# Base = declarative_base()

# class Product(Base):
#     __tablename__ = 'products'

#     name: Mapped[str] = mapped_column(String(100), nullable=False)
#     description: Mapped[str] = mapped_column(Text, nullable=True)
#     price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
#     category: Mapped[str] = mapped_column(String(50), nullable=True)
#     brand: Mapped[str] = mapped_column(String(50), nullable=True)
#     created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

# # Users Table
# class User(Base):
#     __tablename__ = 'users'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     name: Mapped[str] = mapped_column(String, nullable=True)
#     email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
#     password: Mapped[str] = mapped_column(String, nullable=False)
#     role_id: Mapped[str] = mapped_column(ForeignKey('roles.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
#     email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
#     upline_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)  # Self-referential FK
#     last_logged_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

#     sessions: Mapped[list['Session']] = relationship("Session", back_populates="user")


# # Sessions Table
# class Session(Base):
#     __tablename__ = 'sessions'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)  # ForeignKey
#     access_token: Mapped[str] = mapped_column(Text, nullable=False)
#     refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
#     ip_address: Mapped[str] = mapped_column(String, nullable=True)
#     device: Mapped[str] = mapped_column(String, nullable=True)
#     os: Mapped[str] = mapped_column(String, nullable=True)
#     browser: Mapped[str] = mapped_column(String, nullable=True)
#     status: Mapped[str] = mapped_column(String, nullable=False)
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     expires_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

#     user: Mapped[User] = relationship("User", back_populates="sessions")


# # Roles Table
# class Role(Base):
#     __tablename__ = 'roles'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     name: Mapped[str] = mapped_column(String, nullable=False)
#     display_name: Mapped[str] = mapped_column(String, nullable=False)
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

#     permissions: Mapped[list['Permission']] = relationship("Permission", back_populates="role")


# # Permissions Table
# class Permission(Base):
#     __tablename__ = 'permissions'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     name: Mapped[str] = mapped_column(String, nullable=False)
#     display_name: Mapped[str] = mapped_column(String, nullable=False)
#     role_id: Mapped[str] = mapped_column(ForeignKey('roles.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)  # ForeignKey
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

#     role: Mapped[Role] = relationship("Role", back_populates="permissions")


# # Bots Table
# class Bot(Base):
#     __tablename__ = 'bots'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     organization_id: Mapped[str] = mapped_column(ForeignKey('organizations.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)  # ForeignKey
#     name: Mapped[str] = mapped_column(String, nullable=False)
#     description: Mapped[str] = mapped_column(Text, nullable=True)
#     language: Mapped[str] = mapped_column(String, nullable=True)
#     system_message: Mapped[str] = mapped_column(Text, nullable=True)
#     placeholder_message: Mapped[str] = mapped_column(Text, nullable=True)
#     welcome_message: Mapped[str] = mapped_column(Text, nullable=True)
#     starter_questions: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
#     llm_model_id: Mapped[str] = mapped_column(ForeignKey('llm_models.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)  # ForeignKey
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

#     # Unique Index for botId
#     __table_args__ = (
#         Index('bot_configuration_botId_key', 'id', unique=True),
#     )


# # Bot Configuration Table
# class BotConfiguration(Base):
#     __tablename__ = 'bot_configuration'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     bot_id: Mapped[str] = mapped_column(ForeignKey('bots.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, unique=True)  # ForeignKey + Unique
#     avatar_url: Mapped[str] = mapped_column(String, nullable=True)
#     u_avatar_url: Mapped[str] = mapped_column(String, nullable=True)
#     a_avatar_url: Mapped[str] = mapped_column(String, nullable=True)
#     u_message_color: Mapped[str] = mapped_column(String, nullable=True)
#     a_message_color: Mapped[str] = mapped_column(String, nullable=True)
#     font_id: Mapped[str] = mapped_column(String, nullable=False)
#     show_sources: Mapped[bool] = mapped_column(Boolean, nullable=False)
#     send_button_text: Mapped[str] = mapped_column(String, nullable=True)
#     custom_css: Mapped[str] = mapped_column(Text, nullable=True)
#     embed_angle: Mapped[str] = mapped_column(String, nullable=True)
#     embed_widget_size: Mapped[str] = mapped_column(String, nullable=True)
#     embed_widget_icon_url: Mapped[str] = mapped_column(String, nullable=True)
#     embed_auto_open: Mapped[bool] = mapped_column(Boolean, nullable=True)
#     embed_ping_message: Mapped[str] = mapped_column(Text, nullable=True)
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

#     # Unique Index for botId
#     __table_args__ = (
#         Index('bot_configuration_botId_key', 'bot_id', unique=True),
#     )


# # Subscriptions Table
# class Subscription(Base):
#     __tablename__ = 'subscriptions'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     organization_id: Mapped[str] = mapped_column(ForeignKey('organizations.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, unique=True)  # ForeignKey + Unique
#     plan_id: Mapped[str] = mapped_column(ForeignKey('plans.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
#     status: Mapped[str] = mapped_column(String, nullable=False)
#     start_date: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
#     end_date: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

#     # Unique Index for organizationId
#     __table_args__ = (
#         Index('subscriptions_organizationId_key', 'organization_id', unique=True),
#     )


# # Plans Table
# class Plan(Base):
#     __tablename__ = 'plans'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     name: Mapped[str] = mapped_column(String, nullable=False)
#     slug_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # Unique Index
#     billing_cycle: Mapped[BillingCycle] = mapped_column(Enum(BillingCycle), nullable=False, server_default=text("'MONTHLY'"))
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

#     # Unique Index for slugName
#     __table_args__ = (
#         Index('plans_slugName_key', 'slug_name', unique=True),
#     )


# # Payment Methods Table
# class PaymentMethod(Base):
#     __tablename__ = 'payment_methods'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     name: Mapped[str] = mapped_column(String, nullable=False)
#     slug_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # Unique Index
#     status: Mapped[PaymentMethodStatus] = mapped_column(Enum(PaymentMethodStatus), nullable=False, server_default=text("'ACTIVE'"))
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

#     # Unique Index for slugName
#     __table_args__ = (
#         Index('payment_methods_slugName_key', 'slug_name', unique=True),
#     )


# # LLM Models Table
# class LLMModel(Base):
#     __tablename__ = 'llm_models'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     name: Mapped[str] = mapped_column(String, nullable=False)
#     slug_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # Unique Index
#     plan_id: Mapped[str] = mapped_column(ForeignKey('plans.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)  # ForeignKey
#     description: Mapped[str] = mapped_column(Text, nullable=True)
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

#     # Unique Index for slugName
#     __table_args__ = (
#         Index('llm_models_slugName_key', 'slug_name', unique=True),
#     )


# # Techniques Table
# class Technique(Base):
#     __tablename__ = 'techniques'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     name: Mapped[str] = mapped_column(String, nullable=False)
#     slug_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # Unique Index
#     plan_id: Mapped[str] = mapped_column(ForeignKey('plans.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)  # ForeignKey
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

#     # Unique Index for slugName
#     __table_args__ = (
#         Index('techniques_slugName_key', 'slug_name', unique=True),
#     )

# # Invoices Table
# class Invoice(Base):
#     __tablename__ = 'invoices'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     payment_id: Mapped[str] = mapped_column(ForeignKey('payments.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)  # ForeignKey
#     invoice_code: Mapped[str] = mapped_column(String, nullable=False)
#     issued_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
#     due_date: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

# # Organizations Table
# class Organization(Base):
#     __tablename__ = 'organizations'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     name: Mapped[str] = mapped_column(String, nullable=False)
#     plan_id: Mapped[str] = mapped_column(ForeignKey('plans.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)  # ForeignKey
#     owner_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)  # ForeignKey
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

# # Organization Users Table
# class OrganizationUser(Base):
#     __tablename__ = 'organization_users'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     organization_id: Mapped[str] = mapped_column(ForeignKey('organizations.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)  # ForeignKey
#     user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)  # ForeignKey

# # LLM Models Table
# class LLMModel(Base):
#     __tablename__ = 'llm_models'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     name: Mapped[str] = mapped_column(String, nullable=False)
#     slug_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # Unique Index
#     plan_id: Mapped[str] = mapped_column(ForeignKey('plans.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)  # ForeignKey
#     description: Mapped[str] = mapped_column(Text, nullable=True)
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

#     # Unique Index for slugName
#     __table_args__ = (
#         Index('llm_models_slugName_key', 'slug_name', unique=True),
#     )

# # Sources Table
# class Source(Base):
#     __tablename__ = 'sources'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     organization_id: Mapped[str] = mapped_column(ForeignKey('organizations.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)  # ForeignKey
#     technique_id: Mapped[str] = mapped_column(ForeignKey('techniques.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)  # ForeignKey
#     title: Mapped[str] = mapped_column(String, nullable=False)
#     url: Mapped[str] = mapped_column(String, nullable=False)
#     status: Mapped[str] = mapped_column(String, nullable=False)
#     summary: Mapped[str] = mapped_column(Text, nullable=False)
#     content_type: Mapped[str] = mapped_column(String, nullable=False)
#     content_length: Mapped[int] = mapped_column(Integer, nullable=False)
#     content_hash: Mapped[str] = mapped_column(String, nullable=False)
#     sync_time: Mapped[int] = mapped_column(Integer, nullable=False)
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

# # Syncs Table
# class Sync(Base):
#     __tablename__ = 'syncs'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     source_id: Mapped[str] = mapped_column(ForeignKey('sources.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)  # ForeignKey
#     message: Mapped[str] = mapped_column(Text, nullable=True)
#     status: Mapped[str] = mapped_column(String, nullable=False)
#     started_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
#     succeed_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
#     error_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
#     cancelled_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

# # Techniques Table
# class Technique(Base):
#     __tablename__ = 'techniques'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     name: Mapped[str] = mapped_column(String, nullable=False)
#     slug_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # Unique Index
#     plan_id: Mapped[str] = mapped_column(ForeignKey('plans.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)  # ForeignKey
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

#     # Unique Index for slugName
#     __table_args__ = (
#         Index('techniques_slugName_key', 'slug_name', unique=True),
#     )

# # Vectors Table
# class Vector(Base):
#     __tablename__ = 'vectors'

#     id: Mapped[str] = mapped_column(String, primary_key=True)
#     organization_id: Mapped[str] = mapped_column(ForeignKey('organizations.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)  # ForeignKey
#     source_id: Mapped[str] = mapped_column(ForeignKey('sources.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)  # ForeignKey
#     embedding: Mapped[list[float]] = mapped_column(Text, nullable=False)  # Assuming 'vector(1024)' can be stored as a list of floats
#     chunk_content: Mapped[str] = mapped_column(Text, nullable=False)
#     metadata: Mapped[dict] = mapped_column(JSON, nullable=False)
#     chunk_length: Mapped[int] = mapped_column(Integer, nullable=False)
#     created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
#     updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
