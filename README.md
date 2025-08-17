# WhatsApp-like Chat Application

A Python-based chat application with GUI interface, secure message storage, and multi-client support using sockets and threading.

## Features

🔹 **Multi-client chat server** with socket programming  
🔹 **Threaded connections** for concurrent users  
🔹 **PyQt5 GUI client** with modern interface  
🔹 **WhatsApp-like groups** with admin controls  
🔹 **Group creation and management**  
🔹 **Secure message hashing** using SHA-256  
🔹 **Chat history storage** in JSON format  
🔹 **Public, private and group messaging**  

## File Structure

```
chat-app/
├── server.py          # Enhanced chat server with groups
├── client.py          # PyQt5 GUI client
├── chat_viewer.py     # Chat history viewer utility
├── requirements.txt   # Dependencies info
├── server_logs/       # Server chat logs (auto-created)
│   └── groups/        # Group chat logs and info
└── client_logs/       # Client chat logs (auto-created)
    └── groups/        # Client group logs
```

## How to Run

### 1. Start the Server
```bash
python server.py
```
The server will start on `localhost:12345` by default and wait for connections.

### 2. Start Client(s)
```bash
python client.py
```
- A PyQt5 GUI window will open
- Enter server details (localhost:12345 by default)
- Click "Connect" and enter your username
- Click "Manage Groups" to create/manage groups

### 3. View Chat History
```bash
# View chat between two users
python chat_viewer.py --users alice bob

# View group chat
python chat_viewer.py --group developers

# List all available chats
python chat_viewer.py --list-chats

```

## Usage Commands

### In the client GUI:
- **Public message**: Just type normally and press Enter
- **Private message**: `@username your message here`
- **Group message**: `#groupname your message here`
- **Create group**: `/creategroup groupname`
- **Add member**: `/addtogroup groupname username` (admin only)
- **Leave group**: `/leavegroup groupname`
- **List your groups**: `/listgroups`
- **Group members**: `/groupmembers groupname`
- **View online users**: `/users`
- **Quit**: `/quit` or close the window

### Message Hashing
All messages are hashed using SHA-256 for secure storage:
```python
hash = hashlib.sha256(message.encode()).hexdigest()
```

### Chat History Storage
- **Server logs**: `server_logs/{user1}_{user2}_conversation.json`
- **Client logs**: `client_logs/{username}_public_chat.json`
- **Private chats**: `client_logs/{user1}_{user2}_private.json`

Each message entry includes:
```json
{
  "timestamp": "2025-08-17 14:30:45",
  "sender": "alice",
  "receiver": "bob",
  "message": "Hello Bob!",
  "message_hash": "sha256_hash_of_message"
}
```
## Installation

```bash
# Install PyQt5
pip install PyQt5

# Run the application
python server.py  # Start server first
python client.py  # Start client(s)

## License

This is a demonstration project for learning socket programming and GUI development in Python.
