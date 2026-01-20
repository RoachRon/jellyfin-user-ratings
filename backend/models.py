from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Recommendation(Base):
    __tablename__ = "recommendations"

    userId: Mapped[str] = mapped_column(String, primary_key=True)
    itemId: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    userId: Mapped[str | None] = mapped_column(String, nullable=True)
    itemId: Mapped[str | None] = mapped_column(String, nullable=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    globalLimit: Mapped[int | None] = mapped_column(Integer, nullable=True)


class UserSetting(Base):
    __tablename__ = "user_settings"

    userId: Mapped[str] = mapped_column(String, primary_key=True)
    limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
