from enum import StrEnum, nonmember


class Role(StrEnum):
    USER = "user"
    ADMIN = "admin"

    _LEVELS = nonmember(
        {
            USER: 10,
            ADMIN: 20,
        }
    )

    @property
    def level(self) -> int:
        return self._LEVELS[self]
