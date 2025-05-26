from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from Models.BaseModel import BaseModel  # 导入基类
from Models.ActorTagRelationship import ActorTagRelationship  # 导入您的模型
from Models.ActorModel import ActorModel  # 导入您的模型
from Models.ActorGroupModel import ActorGroupModel  # 导入您的模型
from Models.ActorGroupCondModel import ActorGroupCondModel  # 导入您的模型
from Models.ActorMainModel import ActorMainModel  # 导入您的模型
from Models.ActorTagModel import ActorTagModel  # 导入您的模型
from Models.ActorLogModel import ActorLogModel  # 导入您的模型
from Models.NoticeModel import NoticeModel  # 导入您的模型
from Models.PostModel import PostModel  # 导入您的模型
from Models.ResModel import ResModel  # 导入您的模型
from Models.ResDomainModel import ResDomainModel  # 导入您的模型
from Models.ResUrlModel import ResUrlModel  # 导入您的模型
from Models.ActorFileInfoModel import ActorFileInfoModel  # 导入您的模型

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = BaseModel.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
