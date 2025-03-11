import socket
import threading
import typing
from collections import defaultdict
from datetime import datetime

from client.client_chat import ClientInfo
from server.db.chat_db import ChatDB
from server_config import ServerConfig
from utils import RoomTypes


class ChatServer:
    def __init__(self, *, host, listen_port):   #should be init class or not?
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server.bind((host, listen_port))
        except Exception as e:
            print(f"Unable to bind to host and port : {repr(e)}")

        self.server.listen(ServerConfig.listener_limit_number)

        self.active_clients: typing.Set[ClientInfo] = set()
        self.room_name_to_active_clients: typing.DefaultDict[str, typing.List[ClientInfo]] = defaultdict(list)

        self.chat_db = ChatDB(db_path=ServerConfig.db_path)
        self.chat_db.setup_database()

        self.room_setup_done_flag = threading.Event()

    def client_handler(self, conn):
        sender_name = conn.recv(1024).decode('utf-8')
        print(f"Got username {sender_name}")
        self.chat_db.store_user(sender_name=sender_name.strip())

        client_info = ClientInfo(client_conn=conn, username=sender_name)

        print(f"start setup")
        room_setup_thread = threading.Thread(target=self._room_setup, args=(conn, client_info))
        room_setup_thread.start()

        #listen for massages after setup
        print("start listen")
        received_messages_thread = threading.Thread(target=self._receiving_messages, args=(conn, client_info,)) #get client info?
        received_messages_thread.start()

    def _room_setup(self, conn, client_info: ClientInfo):
        while True:
            room_type = conn.recv(1024).decode('utf-8')

            if RoomTypes[room_type.upper()] == RoomTypes.PRIVATE:
                group_name = conn.recv(1024).decode('utf-8')
                received_user_join_timestamp = conn.recv(1024).decode('utf-8')

                user_join_timestamp = self.chat_db.get_user_join_timestamp(
                    sender_name=client_info.username,
                    room_name=group_name,
                    join_timestamp=received_user_join_timestamp)

                self._broadcast_to_all_active_clients_in_room(
                    msg=f"{client_info.username} join to {group_name}",
                    current_room=client_info.current_room,
                    pattern=False
                )
                self.chat_db.create_room(room_name=group_name)
                #users in private will get only messages came after his join timestamps
                self.chat_db.send_previous_messages_in_room(client_info.client_conn, group_name, user_join_timestamp)

            else:
                group_name = room_type
                print(f"sending joining message")
                self._broadcast_to_all_active_clients_in_room(
                    msg=f"{client_info.username} join to {group_name}",
                    current_room=client_info.current_room,
                    pattern=False
                )
                self.chat_db.create_room(room_name=group_name)
                # users in global get all messages ever written
                self.chat_db.send_previous_messages_in_room(client_info.client_conn, group_name)

            client_info.room_type = room_type
            client_info.current_room = group_name
            self.room_name_to_active_clients[group_name].append(client_info)

            client_info.room_setup_done_flag.set()
            print(f"finish room setup")
            break

    def _receiving_messages(self, conn, client_info):
        client_info.room_setup_done_flag.wait()

        while True:
                if msg := conn.recv(2048).decode('utf-8'):
                    if msg == '/switch':
                        self.room_setup_done_flag.clear() #clear flag so all messages send to the setup from this time

                        self._remove_client_in_current_room(current_room=client_info.current_room, sender_username=client_info.username)

                        self._broadcast_to_all_active_clients_in_room(
                            msg=f"{client_info.username} left {client_info.current_room}",
                            current_room=client_info.current_room,
                            pattern=False
                        )

                        self._room_setup(conn, client_info)

                    else:
                        print(f"received message {msg}")
                        msg_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        self._broadcast_to_all_active_clients_in_room(
                            msg=msg,
                            current_room=client_info.current_room,
                            sender_name=client_info.username,
                            msg_timestamp=msg_timestamp
                        )

                        self.chat_db.store_message(text_message=msg, sender_name=client_info.username, room_name=client_info.current_room, timestamp=msg_timestamp)

    def _broadcast_to_all_active_clients_in_room(self, *, msg, current_room, sender_name: typing.Optional[str] = None, msg_timestamp: typing.Optional[str] = None, pattern:typing.Optional[bool] = True):
        if clients_in_room := self.room_name_to_active_clients.get(current_room):
            final_msg = msg
            for client in clients_in_room:
                if client.current_room == current_room:
                    if pattern:
                        final_msg = ServerConfig.message_pattern.format(
                            msg_timestamp=msg_timestamp, sender_name=sender_name, message=msg
                        )
                    client.client_conn.send(final_msg.encode('utf-8'))

    def _remove_client_in_current_room(self, *, current_room, sender_username):
        self.room_name_to_active_clients[current_room] = [client for client in self.room_name_to_active_clients[current_room]
                                                          if client.username != sender_username]

    def start(self):
        print("Server started...")
        while True:
            client_sock, addr = self.server.accept()
            print(f"Successfully connected client {addr[0]} {addr[1]}")
            thread = threading.Thread(target=self.client_handler, args=(client_sock,))
            # thread = threading.Thread(target=self.client_handler, kwargs={"conn":client_sock})  #probably better?
            thread.start()

def main():
    server = ChatServer(host='127.0.0.1', listen_port=2)
    server.start()


if __name__ == '__main__':
    main()
