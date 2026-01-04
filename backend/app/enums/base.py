from enum import IntEnum

class BaseEnum(IntEnum):

    @classmethod
    def dict(cls):
        return {
            item.name: item.meta()
            for item in cls
        }

    def meta(self):
        """
        子类实现
        """
        raise NotImplementedError




"""
Example Usage:

class UserStatus(BaseEnum):
    DISABLED = 0
    ACTIVE = 1
    BANNED = 2

    def meta(self):
        return {
            "value": self.value,
            "label": {
                UserStatus.DISABLED: "禁用",
                UserStatus.ACTIVE: "正常",
                UserStatus.BANNED: "封禁",
            }[self],
            "color": {
                UserStatus.DISABLED: "gray",
                UserStatus.ACTIVE: "green",
                UserStatus.BANNED: "red",
            }[self],
        }


"""