from io import BytesIO
from struct import pack

from telethon.tl.tlobject import TLRequest
from telethon.tl.types import InputUser


class GetUserStarGiftsRequest(TLRequest):
    """Manual implementation of ``payments.getUserStarGifts``."""

    __slots__ = ("user_id", "offset", "limit")

    CONSTRUCTOR_ID = 0x5e72c7e1
    SUBCLASS_OF_ID = 0x00000000

    def __init__(self, user_id: InputUser, offset: str = "", limit: int = 100):
        self.user_id = user_id
        self.offset = offset
        self.limit = limit

    def write(self):
        """Serialize the request according to MTProto."""
        b = BytesIO()
        b.write(pack("<I", self.CONSTRUCTOR_ID))
        b.write(self.user_id.write())
        offset_bytes = self.offset.encode("utf-8")
        b.write(pack("<I", len(offset_bytes)))
        b.write(offset_bytes)
        while b.tell() % 4:
            b.write(b"\x00")
        b.write(pack("<i", self.limit))
        return b.getvalue()

    def read(self, b, *args):  # type: ignore[override]
        """Return the raw bytes for further manual parsing."""
        return b.read()
