from tortoise import fields, models


class User(models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=40, null=False, unique=True, description="Username")
    password = fields.CharField(max_length=30, null=False, unique=False, description="Password")
    email = fields.CharField(max_length=50, null=False,  unique=True, description="Email")
    alias = fields.CharField(max_length=50, null=False, default="Momo", unique=False, description="Alias")
    created_at = fields.DatetimeField(auto_now_add=True, description="Created at")
    updated_at = fields.DatetimeField(auto_now=True, description="Updated at")
    birthdate = fields.DateField(null=False, default="1990-01-01", description="Birthdate")
    gender = fields.IntField(null=False, description="Gender, man 0, woman 1, other 2")
    phone = fields.CharField(max_length=20, null=True, unique=False, description="Phone number")
    address = fields.CharField(max_length=100, null=True, unique=False, description="Address")
    city = fields.CharField(max_length=50, null=True, unique=False, description="City")
    is_active = fields.BooleanField(default=True, description="Is active")
    countryCode = fields.CharField(max_length=5, null=True, unique=False, description="Country Code")
    avatar = fields.CharField(max_length=200, null=True, unique=False, description="Avatar")

    async def save(self, *args, **kwargs):
        pass