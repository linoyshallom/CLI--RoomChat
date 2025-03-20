import enum

class RoomTypes(enum.Enum):
    GLOBAL = "GLOBAL"
    PRIVATE = "PRIVATE"


class MessageTypes(enum.Enum):
    SYSTEM = "SYSTEM"
    CHAT = "CHAT"


class FileHandlerTypes(enum.Enum):
    UPLOAD = "UPLOAD"
    DOWNLOAD = "DOWNLOAD"

#class FileTransferStatus: succeed, failed, notfound

if __name__ == "__main__":
    try:
       print(FileHandlerTypes.UPLOAD)
       # FileHandlerTypes["UPLOAD"]
    except Exception as e:
        raise e