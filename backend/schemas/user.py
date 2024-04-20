from tortoise.contrib.pydantic import pydantic_model_creator
from models import User

# Create Pydantic models for User, excluding password_hash, created_at, and updated_at fields.
User_Pydantic = pydantic_model_creator(User, name="User", exclude=("password", "created_at", "updated_at"))
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn")