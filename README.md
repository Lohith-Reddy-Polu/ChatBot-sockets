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
🔹 **Tabbed interface** for different chat types  
🔹 **Real-time message display**  
🔹 **User and group management**  
🔹 **Chat viewer utility** for viewing complete histories  
🔹 **Search functionality** across all chats  
🔹 **Export chats** to text files  

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
- Use the tabbed interface for different chat types
- Click "Manage Groups" to create/manage groups

### 3. View Chat History
```bash
# View chat between two users
python chat_viewer.py --users alice bob

# View group chat
python chat_viewer.py --group developers

# List all available chats
python chat_viewer.py --list-chats

# List all groups
python chat_viewer.py --list-groups

# Search messages
python chat_viewer.py --search "hello world"

# Export chat to file
python chat_viewer.py --users alice bob --export alice_bob_chat.txt

# Show message hashes for verification
python chat_viewer.py --group developers --show-hash
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

### Group Management Features:
- Only group admins can add new members
- Members can leave groups anytime
- If admin leaves, another member becomes admin automatically
- Empty groups are automatically deleted
- Group info is stored separately from chat history

## Chat Viewer Utility

### Command Options:
```bash
# View specific conversations
python chat_viewer.py --users user1 user2
python chat_viewer.py --group groupname

# List available chats
python chat_viewer.py --list-chats
python chat_viewer.py --list-groups

# Search functionality
python chat_viewer.py --search "search term"
python chat_viewer.py --search "hello" --search-type group

# Export and verification
python chat_viewer.py --users alice bob --export chat.txt
python chat_viewer.py --group team --show-hash
```

### Search Types:
- `all` - Search in both direct and group chats (default)
- `direct` - Search only in direct chats
- `group` - Search only in group chats

## Security Features

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

## Technical Details

### Server Architecture
- **Socket server** listening for connections
- **Threading** for each client connection
- **Message broadcasting** to all connected clients
- **Private messaging** between specific users
- **JSON-based** chat history storage

### Client Architecture
- **Tkinter GUI** with WhatsApp-like design
- **Threading** for receiving messages
- **Real-time** message display
- **Local chat history** storage
- **Connection management**

### Network Protocol
- **TCP sockets** for reliable communication
- **UTF-8 encoding** for message transmission
- **Simple text protocol** for commands and messages

## Customization

### Change Server Settings
In `server.py`, modify:
```python
server = ChatServer(host='your_host', port=your_port)
```

### GUI Styling
The client uses WhatsApp-inspired colors:
- Background: `#075E54` (dark green)
- Chat area: `#ECE5DD` (light beige)
- Send button: `#25D366` (green)

### Storage Location
Chat logs are automatically created in:
- `server_logs/` - Server-side conversation logs
- `client_logs/` - Client-side message history

## Troubleshooting

### Connection Issues
- Ensure server is running first
- Check firewall settings
- Verify host/port configuration

### Username Conflicts
- Each username must be unique
- Server will reject duplicate usernames

### GUI Issues
- Requires Python with Tkinter support
- On Linux: `sudo apt-get install python3-tk`

## Security Considerations

1. **Message hashing** provides data integrity verification
2. **Local storage** keeps chat history on each machine
3. **No encryption** - messages are sent in plain text over network
4. **Authentication** is basic username-based

## Future Enhancements

- Message encryption (AES/RSA)
- File sharing capabilities
- Group chat rooms
- User authentication system
- Message timestamps synchronization
- Emoji support
- Audio/video calling

## Requirements

- Python 3.6+
- PyQt5 (`pip install PyQt5`)

## Installation

```bash
# Install PyQt5
pip install PyQt5

# Run the application
python server.py  # Start server first
python client.py  # Start client(s)

## License

This is a demonstration project for learning socket programming and GUI development in Python.