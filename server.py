import socket
import threading
import json
import hashlib
import datetime
import os
from typing import Dict, List, Set

class ChatServer:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.clients: Dict[socket.socket, str] = {}
        self.client_names: Dict[str, socket.socket] = {}
        self.groups: Dict[str, Set[str]] = {}  # group_name -> set of usernames
        self.group_admins: Dict[str, str] = {}  # group_name -> admin_username
        self.server_socket = None
        self.chat_history: Dict[str, List] = {}
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('server_logs'):
            os.makedirs('server_logs')
        if not os.path.exists('server_logs/groups'):
            os.makedirs('server_logs/groups')
    
    def hash_message(self, message: str) -> str:
        """Hash message for secure storage"""
        return hashlib.sha256(message.encode()).hexdigest()
    
    def save_chat_history(self, sender: str, receiver: str, message: str, message_type="direct"):
        """Save chat history to file with hashing"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        chat_entry = {
            'timestamp': timestamp,
            'sender': sender,
            'receiver': receiver,
            'message': message,
            'message_hash': self.hash_message(message),
            'type': message_type
        }
        
        if message_type == "group":
            # Group message
            filename = f"server_logs/groups/{receiver}_group.json"
        else:
            # Direct message - Create a conversation key (sorted to ensure consistency)
            participants = sorted([sender, receiver])
            filename = f"server_logs/{participants[0]}_{participants[1]}_conversation.json"
        
        try:
            with open(filename, 'r') as f:
                history = json.load(f)
        except FileNotFoundError:
            history = []
        
        history.append(chat_entry)
        
        with open(filename, 'w') as f:
            json.dump(history, f, indent=2)
    
    def create_group(self, admin_name: str, group_name: str) -> str:
        """Create a new group"""
        if group_name in self.groups:
            return f"Group '{group_name}' already exists"
        
        self.groups[group_name] = {admin_name}
        self.group_admins[group_name] = admin_name
        
        # Save group info
        self.save_group_info(group_name)
        
        return f"Group '{group_name}' created successfully. You are the admin."
    
    def add_to_group(self, admin_name: str, group_name: str, username: str) -> str:
        """Add user to group (only admin can do this)"""
        if group_name not in self.groups:
            return f"Group '{group_name}' does not exist"
        
        if self.group_admins[group_name] != admin_name:
            return f"Only the admin can add members to '{group_name}'"
        
        if username not in self.client_names:
            return f"User '{username}' is not online"
        
        if username in self.groups[group_name]:
            return f"User '{username}' is already in the group"
        
        self.groups[group_name].add(username)
        self.save_group_info(group_name)
        
        # Notify the added user
        user_socket = self.client_names[username]
        notification = f"You have been added to group '{group_name}' by {admin_name}"
        try:
            user_socket.send(notification.encode('utf-8'))
        except:
            pass
        
        # Notify group members
        group_notification = f"{username} has been added to the group by {admin_name}"
        self.send_group_message(group_notification, group_name, "SYSTEM")
        
        return f"User '{username}' added to group '{group_name}'"
    
    def leave_group(self, username: str, group_name: str) -> str:
        """Remove user from group"""
        if group_name not in self.groups:
            return f"Group '{group_name}' does not exist"
        
        if username not in self.groups[group_name]:
            return f"You are not a member of group '{group_name}'"
        
        self.groups[group_name].remove(username)
        
        # If admin leaves and group has other members, assign new admin
        if self.group_admins[group_name] == username and self.groups[group_name]:
            new_admin = next(iter(self.groups[group_name]))
            self.group_admins[group_name] = new_admin
            
            # Notify new admin
            if new_admin in self.client_names:
                admin_socket = self.client_names[new_admin]
                notification = f"You are now the admin of group '{group_name}'"
                try:
                    admin_socket.send(notification.encode('utf-8'))
                except:
                    pass
        
        # If group becomes empty, delete it
        if not self.groups[group_name]:
            del self.groups[group_name]
            del self.group_admins[group_name]
            # Delete group info file
            group_info_file = f"server_logs/groups/{group_name}_info.json"
            if os.path.exists(group_info_file):
                os.remove(group_info_file)
            return f"Left group '{group_name}'. Group was deleted as it became empty."
        else:
            self.save_group_info(group_name)
            # Notify group members
            group_notification = f"{username} has left the group"
            self.send_group_message(group_notification, group_name, "SYSTEM")
            return f"Left group '{group_name}'"
    
    def save_group_info(self, group_name: str):
        """Save group information to file"""
        group_info = {
            'group_name': group_name,
            'admin': self.group_admins[group_name],
            'members': list(self.groups[group_name]),
            'created_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        filename = f"server_logs/groups/{group_name}_info.json"
        with open(filename, 'w') as f:
            json.dump(group_info, f, indent=2)
    
    def send_group_message(self, message: str, group_name: str, sender_name: str):
        """Send message to all group members"""
        if group_name not in self.groups:
            return f"Group '{group_name}' does not exist"
        
        if sender_name != "SYSTEM" and sender_name not in self.groups[group_name]:
            return f"You are not a member of group '{group_name}'"
        
        # Format message
        if sender_name == "SYSTEM":
            full_message = f"[{group_name}] {message}"
        else:
            full_message = f"[{group_name}] {sender_name}: {message}"
        
        # Send to all group members except sender
        sent_count = 0
        for member in self.groups[group_name]:
            if member in self.client_names and member != sender_name:
                try:
                    member_socket = self.client_names[member]
                    member_socket.send(full_message.encode('utf-8'))
                    sent_count += 1
                except:
                    pass
        
        # Save to group history
        if sender_name != "SYSTEM":
            self.save_chat_history(sender_name, group_name, message, "group")
        
        return f"Message sent to {sent_count} group members"
    
    def list_groups(self, username: str) -> str:
        """List all groups user is member of"""
        user_groups = [group for group, members in self.groups.items() if username in members]
        if user_groups:
            groups_info = []
            for group in user_groups:
                admin = self.group_admins[group]
                member_count = len(self.groups[group])
                groups_info.append(f"{group} (Admin: {admin}, Members: {member_count})")
            return "Your groups:\n" + "\n".join(groups_info)
        else:
            return "You are not a member of any groups"
    
    def list_group_members(self, username: str, group_name: str) -> str:
        """List members of a specific group"""
        if group_name not in self.groups:
            return f"Group '{group_name}' does not exist"
        
        if username not in self.groups[group_name]:
            return f"You are not a member of group '{group_name}'"
        
        members = list(self.groups[group_name])
        admin = self.group_admins[group_name]
        
        member_list = []
        for member in members:
            if member == admin:
                member_list.append(f"{member} (Admin)")
            else:
                member_list.append(member)
        
        return f"Members of '{group_name}':\n" + "\n".join(member_list)
    
    def broadcast_message(self, message: str, sender_socket: socket.socket):
        """Broadcast message to all connected clients except sender"""
        sender_name = self.clients.get(sender_socket, "Unknown")
        
        for client_socket, client_name in self.clients.items():
            if client_socket != sender_socket:
                try:
                    full_message = f"{sender_name}: {message}"
                    client_socket.send(full_message.encode('utf-8'))
                    
                    # Save chat history
                    self.save_chat_history(sender_name, client_name, message)
                except:
                    # Remove disconnected client
                    self.remove_client(client_socket)
    
    def send_private_message(self, message: str, sender_socket: socket.socket, target_name: str):
        """Send private message to specific client"""
        sender_name = self.clients.get(sender_socket, "Unknown")
        
        if target_name in self.client_names:
            target_socket = self.client_names[target_name]
            try:
                private_msg = f"[Private] {sender_name}: {message}"
                target_socket.send(private_msg.encode('utf-8'))
                
                # Send confirmation to sender
                confirmation = f"[Private to {target_name}]: {message}"
                sender_socket.send(confirmation.encode('utf-8'))
                
                # Save chat history
                self.save_chat_history(sender_name, target_name, message)
                
            except:
                sender_socket.send(f"Error: Could not send message to {target_name}".encode('utf-8'))
        else:
            sender_socket.send(f"Error: User {target_name} not found".encode('utf-8'))
    
    def remove_client(self, client_socket: socket.socket):
        """Remove client from server"""
        if client_socket in self.clients:
            client_name = self.clients[client_socket]
            del self.clients[client_socket]
            if client_name in self.client_names:
                del self.client_names[client_name]
            
            # Notify other clients
            disconnect_msg = f"{client_name} has left the chat"
            for socket_client in self.clients:
                try:
                    socket_client.send(disconnect_msg.encode('utf-8'))
                except:
                    pass
            
            print(f"Client {client_name} disconnected")
    
    def handle_client(self, client_socket: socket.socket, address):
        """Handle individual client connection"""
        try:
            # Get client name
            client_socket.send("Enter your username: ".encode('utf-8'))
            username = client_socket.recv(1024).decode('utf-8').strip()
            
            # Check if username is already taken
            if username in self.client_names:
                client_socket.send("Username already taken. Please try again.".encode('utf-8'))
                client_socket.close()
                return
            
            # Register client
            self.clients[client_socket] = username
            self.client_names[username] = client_socket
            
            print(f"Client {username} connected from {address}")
            
            # Notify all clients about new connection
            join_msg = f"{username} has joined the chat"
            for socket_client in self.clients:
                if socket_client != client_socket:
                    try:
                        socket_client.send(join_msg.encode('utf-8'))
                    except:
                        pass
            
            # Send welcome message and instructions
            welcome_msg = f"""Welcome to the chat, {username}!
Commands:
- Type normally for public messages
- Use @username message for private messages
- Use #groupname message for group messages
- /creategroup groupname - Create a new group
- /addtogroup groupname username - Add user to group (admin only)
- /leavegroup groupname - Leave a group
- /listgroups - List your groups
- /groupmembers groupname - List group members
- /users - See online users
- /quit - Leave chat"""
            client_socket.send(welcome_msg.encode('utf-8'))
            
            # Handle client messages
            while True:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                
                if message.startswith('/quit'):
                    break
                elif message.startswith('/users'):
                    users_list = "Online users: " + ", ".join(self.client_names.keys())
                    client_socket.send(users_list.encode('utf-8'))
                elif message.startswith('/creategroup '):
                    group_name = message[13:].strip()
                    if group_name:
                        response = self.create_group(username, group_name)
                        client_socket.send(response.encode('utf-8'))
                    else:
                        client_socket.send("Usage: /creategroup groupname".encode('utf-8'))
                elif message.startswith('/addtogroup '):
                    parts = message[12:].split(' ', 1)
                    if len(parts) == 2:
                        group_name, target_user = parts
                        response = self.add_to_group(username, group_name.strip(), target_user.strip())
                        client_socket.send(response.encode('utf-8'))
                    else:
                        client_socket.send("Usage: /addtogroup groupname username".encode('utf-8'))
                elif message.startswith('/leavegroup '):
                    group_name = message[12:].strip()
                    if group_name:
                        response = self.leave_group(username, group_name)
                        client_socket.send(response.encode('utf-8'))
                    else:
                        client_socket.send("Usage: /leavegroup groupname".encode('utf-8'))
                elif message.startswith('/listgroups'):
                    response = self.list_groups(username)
                    client_socket.send(response.encode('utf-8'))
                elif message.startswith('/groupmembers '):
                    group_name = message[14:].strip()
                    if group_name:
                        response = self.list_group_members(username, group_name)
                        client_socket.send(response.encode('utf-8'))
                    else:
                        client_socket.send("Usage: /groupmembers groupname".encode('utf-8'))
                elif message.startswith('@'):
                    # Private message
                    parts = message[1:].split(' ', 1)
                    if len(parts) >= 2:
                        target_user, private_msg = parts
                        self.send_private_message(private_msg, client_socket, target_user)
                    else:
                        client_socket.send("Invalid private message format. Use: @username message".encode('utf-8'))
                elif message.startswith('#'):
                    # Group message
                    parts = message[1:].split(' ', 1)
                    if len(parts) >= 2:
                        group_name, group_msg = parts
                        response = self.send_group_message(group_msg, group_name, username)
                        # Send confirmation to sender
                        client_socket.send(f"[{group_name}] {username}: {group_msg}".encode('utf-8'))
                    else:
                        client_socket.send("Invalid group message format. Use: #groupname message".encode('utf-8'))
                else:
                    # Public message
                    self.broadcast_message(message, client_socket)
                    
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            self.remove_client(client_socket)
            client_socket.close()
    
    def start_server(self):
        """Start the chat server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            print(f"Server started on {self.host}:{self.port}")
            print("Waiting for connections...")
            
            while True:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

if __name__ == "__main__":
    server = ChatServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
        if server.server_socket:
            server.server_socket.close()