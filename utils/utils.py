import dataclasses
import enum
import socket
import threading
import typing
from typing import IO

class RoomTypes(enum.Enum):
    GLOBAL = "GLOBAL"
    PRIVATE = "PRIVATE"

@dataclasses.dataclass
class ClientInfo:
    client_conn: socket.socket
    username: str
    room_type: RoomTypes = None
    current_room: typing.Optional[str] = None
    room_setup_done_flag: threading.Event = dataclasses.field(default_factory=threading.Event)

class MessageTypes(enum.Enum):
    SYSTEM = "SYSTEM"
    CHAT = "REGULAR"

@dataclasses.dataclass
class MessageInfo:
    type: MessageTypes
    text_message: str
    sender_name: typing.Optional[str] = None
    msg_timestamp: typing.Optional[str] = None

    def formatted_msg(self) -> str:
        if self.type == MessageTypes.SYSTEM:
            return f"[SYSTEM]: {self.text_message}"

        else:
            return f"[{self.msg_timestamp}] [{self.sender_name}]: {self.text_message}"



#todo instead utils add to common folder and add structs file?

def chunkify(*, reader_file: IO[bytes], chunk_size: typing.Optional[int] = 65_536) -> typing.Generator[bytes, None, None]:
    while True:
        chunk = reader_file.read(chunk_size)

        if not chunk:
            break

        yield chunk
