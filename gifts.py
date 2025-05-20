from telethon.tl.tlobject import TLRequest
from telethon.tl.types import InputUser


class GetUserStarGiftsRequest(TLRequest):
    """Manual implementation of payments.getUserStarGifts"""

    __slots__ = ["user_id", "offset", "limit"]

    CONSTRUCTOR_ID = 0x5e72c7e1
    SUBCLASS_OF_ID = 0x0

    def __init__(self, user_id: InputUser, offset: str = "", limit: int = 100):
        self.user_id = user_id
        self.offset = offset
        self.limit = limit

    def write(self):
        writer = self._writer
        writer.write_int(self.CONSTRUCTOR_ID, signed=False)
        writer.write(self.user_id.write())
        writer.write_string(self.offset)
        writer.write_int(self.limit)
        return writer.get_bytes()

    def read(self):
        return self._reader.read()
