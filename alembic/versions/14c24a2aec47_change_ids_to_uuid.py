"""change ids to uuid

Revision ID: 14c24a2aec47
Revises: e1bce7481d89
Create Date: 2025-10-28 00:50:38.413753

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '14c24a2aec47'
down_revision: Union[str, Sequence[str], None] = 'e1bce7481d89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema by converting IDs to UUID."""
    # Drop existing foreign key constraints first
    op.drop_constraint('fk_token_user_id_user', 'token', type_='foreignkey')
    op.drop_constraint('fk_otpcode_user_id_user', 'otpcode', type_='foreignkey')
    
    # Create UUID columns
    op.add_column('user', sa.Column('uuid_id', postgresql.UUID(as_uuid=True)))
    op.add_column('token', sa.Column('uuid_id', postgresql.UUID(as_uuid=True)))
    op.add_column('token', sa.Column('uuid_user_id', postgresql.UUID(as_uuid=True)))
    op.add_column('otpcode', sa.Column('uuid_id', postgresql.UUID(as_uuid=True)))
    op.add_column('otpcode', sa.Column('uuid_user_id', postgresql.UUID(as_uuid=True)))

    # Generate UUIDs for existing records
    connection = op.get_bind()
    
    # Update user table
    connection.execute(sa.text(
        "UPDATE \"user\" SET uuid_id = uuid_generate_v4() WHERE uuid_id IS NULL"
    ))
    
    # Update token table with new UUIDs and link to user UUIDs
    connection.execute(sa.text("""
        UPDATE token t 
        SET uuid_id = uuid_generate_v4(),
            uuid_user_id = u.uuid_id
        FROM "user" u 
        WHERE t.user_id = u.id AND t.uuid_id IS NULL
    """))
    
    # Update otpcode table with new UUIDs and link to user UUIDs
    connection.execute(sa.text("""
        UPDATE otpcode o 
        SET uuid_id = uuid_generate_v4(),
            uuid_user_id = u.uuid_id
        FROM "user" u 
        WHERE o.user_id = u.id AND o.uuid_id IS NULL
    """))

    # Drop old columns and rename new ones
    # User table
    op.drop_column('user', 'id')
    op.alter_column('user', 'uuid_id', new_column_name='id', nullable=False)
    op.execute('ALTER TABLE "user" ADD PRIMARY KEY (id)')
    
    # Token table
    op.drop_column('token', 'id')
    op.drop_column('token', 'user_id')
    op.alter_column('token', 'uuid_id', new_column_name='id', nullable=False)
    op.alter_column('token', 'uuid_user_id', new_column_name='user_id', nullable=False)
    op.execute('ALTER TABLE token ADD PRIMARY KEY (id)')
    op.create_foreign_key(None, 'token', 'user', ['user_id'], ['id'], ondelete='CASCADE')
    
    # OTP table
    op.drop_column('otpcode', 'id')
    op.drop_column('otpcode', 'user_id')
    op.alter_column('otpcode', 'uuid_id', new_column_name='id', nullable=False)
    op.alter_column('otpcode', 'uuid_user_id', new_column_name='user_id', nullable=False)
    op.execute('ALTER TABLE otpcode ADD PRIMARY KEY (id)')
    op.create_foreign_key(None, 'otpcode', 'user', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema back to integer IDs."""
    # Create integer ID columns
    op.add_column('user', sa.Column('int_id', sa.Integer()))
    op.add_column('token', sa.Column('int_id', sa.Integer()))
    op.add_column('token', sa.Column('int_user_id', sa.Integer()))
    op.add_column('otpcode', sa.Column('int_id', sa.Integer()))
    op.add_column('otpcode', sa.Column('int_user_id', sa.Integer()))

    # Generate sequential IDs for existing records
    connection = op.get_bind()
    
    # Update user table with sequential IDs
    connection.execute(sa.text("""
        WITH numbered_rows AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as rnum 
            FROM "user"
        )
        UPDATE "user" u 
        SET int_id = nr.rnum 
        FROM numbered_rows nr 
        WHERE u.id = nr.id
    """))
    
    # Update token and otpcode tables with new integer IDs
    connection.execute(sa.text("""
        UPDATE token t 
        SET int_id = ROW_NUMBER() OVER (ORDER BY created_at),
            int_user_id = u.int_id
        FROM "user" u 
        WHERE t.user_id = u.id
    """))
    
    connection.execute(sa.text("""
        UPDATE otpcode o 
        SET int_id = ROW_NUMBER() OVER (ORDER BY created_at),
            int_user_id = u.int_id
        FROM "user" u 
        WHERE o.user_id = u.id
    """))

    # Drop foreign keys first
    op.drop_constraint('token_user_id_fkey', 'token', type_='foreignkey')
    op.drop_constraint('otpcode_user_id_fkey', 'otpcode', type_='foreignkey')
    
    # Drop old columns and rename new ones
    # User table
    op.drop_column('user', 'id')
    op.alter_column('user', 'int_id', new_column_name='id', nullable=False)
    op.execute('ALTER TABLE "user" ADD PRIMARY KEY (id)')
    
    # Token table
    op.drop_column('token', 'id')
    op.drop_column('token', 'user_id')
    op.alter_column('token', 'int_id', new_column_name='id', nullable=False)
    op.alter_column('token', 'int_user_id', new_column_name='user_id', nullable=False)
    op.execute('ALTER TABLE token ADD PRIMARY KEY (id)')
    op.create_foreign_key(None, 'token', 'user', ['user_id'], ['id'], ondelete='CASCADE')
    
    # OTP table
    op.drop_column('otpcode', 'id')
    op.drop_column('otpcode', 'user_id')
    op.alter_column('otpcode', 'int_id', new_column_name='id', nullable=False)
    op.alter_column('otpcode', 'int_user_id', new_column_name='user_id', nullable=False)
    op.execute('ALTER TABLE otpcode ADD PRIMARY KEY (id)')
    op.create_foreign_key(None, 'otpcode', 'user', ['user_id'], ['id'], ondelete='CASCADE')
