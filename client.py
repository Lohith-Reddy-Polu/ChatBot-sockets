import socket
import threading
import sys
import json
import hashlib
import datetime
import os
from typing import Dict, List

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                            QLabel, QFrame, QMessageBox, QInputDialog, QSplitter,
                            QGroupBox, QGridLayout, QStatusBar, QTabWidget,
                            QListWidget, QDialog, QDialogButtonBox, QCheckBox,
                            QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QIcon

class GroupManagementDialog(QDialog):
    """Dialog for managing groups"""
    def __init__(self, parent, client_gui):
        super().__init__(parent)
        self.client_gui = client_gui
        self.setWindowTitle("Group Management")
        self.setGeometry(200, 200, 500, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Create group section
        create_group = QGroupBox("Create New Group")
        create_layout = QHBoxLayout(create_group)
        
        self.group_name_input = QLineEdit()
        self.group_name_input.setPlaceholderText("Enter group name")
        create_layout.addWidget(QLabel("Group Name:"))
        create_layout.addWidget(self.group_name_input)
        
        create_btn = QPushButton("Create Group")
        create_btn.clicked.connect(self.create_group)
        create_layout.addWidget(create_btn)
        
        layout.addWidget(create_group)
        
        # Add member section
        add_member_group = QGroupBox("Add Member to Group")
        add_layout = QGridLayout(add_member_group)
        
        self.target_group_input = QLineEdit()
        self.target_group_input.setPlaceholderText("Group name")
        add_layout.addWidget(QLabel("Group:"), 0, 0)
        add_layout.addWidget(self.target_group_input, 0, 1)
        
        self.target_user_input = QLineEdit()
        self.target_user_input.setPlaceholderText("Username to add")
        add_layout.addWidget(QLabel("Username:"), 1, 0)
        add_layout.addWidget(self.target_user_input, 1, 1)
        
        add_member_btn = QPushButton("Add Member")
        add_member_btn.clicked.connect(self.add_member)
        add_layout.addWidget(add_member_btn, 2, 0, 1, 2)
        
        layout.addWidget(add_member_group)
        
        # Leave group section
        leave_group_section = QGroupBox("Leave Group")
        leave_layout = QHBoxLayout(leave_group_section)
        
        self.leave_group_input = QLineEdit()
        self.leave_group_input.setPlaceholderText("Group name to leave")
        leave_layout.addWidget(QLabel("Group:"))
        leave_layout.addWidget(self.leave_group_input)
        
        leave_btn = QPushButton("Leave Group")
        leave_btn.clicked.connect(self.leave_group)
        leave_layout.addWidget(leave_btn)
        
        layout.addWidget(leave_group_section)
        
        # Quick commands section
        commands_group = QGroupBox("Quick Commands")
        commands_layout = QVBoxLayout(commands_group)
        
        list_groups_btn = QPushButton("List My Groups")
        list_groups_btn.clicked.connect(self.list_groups)
        commands_layout.addWidget(list_groups_btn)
        
        self.group_members_input = QLineEdit()
        self.group_members_input.setPlaceholderText("Group name")
        group_members_layout = QHBoxLayout()
        group_members_layout.addWidget(self.group_members_input)
        
        list_members_btn = QPushButton("List Members")
        list_members_btn.clicked.connect(self.list_group_members)
        group_members_layout.addWidget(list_members_btn)
        
        commands_layout.addLayout(group_members_layout)
        layout.addWidget(commands_group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def create_group(self):
        group_name = self.group_name_input.text().strip()
        if group_name:
            self.client_gui.send_command(f"/creategroup {group_name}")
            self.group_name_input.clear()
    
    def add_member(self):
        group_name = self.target_group_input.text().strip()
        username = self.target_user_input.text().strip()
        if group_name and username:
            self.client_gui.send_command(f"/addtogroup {group_name} {username}")
            self.target_user_input.clear()
    
    def leave_group(self):
        group_name = self.leave_group_input.text().strip()
        if group_name:
            self.client_gui.send_command(f"/leavegroup {group_name}")
            self.leave_group_input.clear()
    
    def list_groups(self):
        self.client_gui.send_command("/listgroups")
    
    def list_group_members(self):
        group_name = self.group_members_input.text().strip()
        if group_name:
            self.client_gui.send_command(f"/groupmembers {group_name}")

class MessageReceiver(QThread):
    """Thread for receiving messages from server"""
    message_received = pyqtSignal(str)
    connection_lost = pyqtSignal()
    
    def __init__(self, socket_obj):
        super().__init__()
        self.socket = socket_obj
        self.running = True
    
    def run(self):
        while self.running and self.socket:
            try:
                message = self.socket.recv(1024).decode('utf-8')
                if not message:
                    break
                self.message_received.emit(message)
            except Exception as e:
                if self.running:
                    self.connection_lost.emit()
                break
    
    def stop(self):
        self.running = False

class ChatClientGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.socket = None
        self.username = ""
        self.connected = False
        self.message_receiver = None
        self.chat_history: Dict[str, List] = {}
        
        # Create client logs directory
        if not os.path.exists('client_logs'):
            os.makedirs('client_logs')
        if not os.path.exists('client_logs/groups'):
            os.makedirs('client_logs/groups')
        
        self.init_ui()
        self.apply_whatsapp_style()
        self.load_chat_history()
    
    def hash_message(self, message: str) -> str:
        """Hash message for secure storage"""
        return hashlib.sha256(message.encode()).hexdigest()
    
    def save_chat_history(self, sender: str, receiver: str, message: str, message_type="direct"):
        """Save chat history to local file with hashing"""
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
            filename = f"client_logs/groups/{receiver}_group.json"
        elif receiver == "Public":
            filename = f"client_logs/{self.username}_public_chat.json"
        else:
            participants = sorted([sender, receiver])
            filename = f"client_logs/{participants[0]}_{participants[1]}_private.json"
        
        try:
            with open(filename, 'r') as f:
                history = json.load(f)
        except FileNotFoundError:
            history = []
        
        history.append(chat_entry)
        
        with open(filename, 'w') as f:
            json.dump(history, f, indent=2)
    
    def load_chat_history(self):
        """Load existing chat history"""
        try:
            if self.username:
                # Load public chat history
                public_file = f"client_logs/{self.username}_public_chat.json"
                if os.path.exists(public_file):
                    with open(public_file, 'r') as f:
                        history = json.load(f)
                        for entry in history[-20:]:  # Load last 20 messages
                            self.display_message(f"[{entry['timestamp']}] {entry['sender']}: {entry['message']}", 
                                               is_history=True)
        except Exception as e:
            print(f"Error loading chat history: {e}")
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("WhatsApp-like Chat with Groups")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Connection frame
        self.create_connection_frame(main_layout)
        
        # Create tabbed interface
        self.create_tabbed_interface(main_layout)
        
        # Message input frame
        self.create_message_input_frame(main_layout)
        
        # Commands info
        self.create_commands_frame(main_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Not connected")
    
    def create_connection_frame(self, parent_layout):
        """Create connection controls"""
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QGridLayout(conn_group)
        
        # Server settings
        conn_layout.addWidget(QLabel("Server:"), 0, 0)
        self.host_entry = QLineEdit("localhost")
        self.host_entry.setMaximumWidth(150)
        conn_layout.addWidget(self.host_entry, 0, 1)
        
        conn_layout.addWidget(QLabel("Port:"), 0, 2)
        self.port_entry = QLineEdit("12345")
        self.port_entry.setMaximumWidth(80)
        conn_layout.addWidget(self.port_entry, 0, 3)
        
        # Connection buttons
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_to_server)
        conn_layout.addWidget(self.connect_btn, 0, 4)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect)
        self.disconnect_btn.setEnabled(False)
        conn_layout.addWidget(self.disconnect_btn, 0, 5)
        
        # Group management button
        self.group_mgmt_btn = QPushButton("Manage Groups")
        self.group_mgmt_btn.clicked.connect(self.open_group_management)
        self.group_mgmt_btn.setEnabled(False)
        conn_layout.addWidget(self.group_mgmt_btn, 0, 6)
        
        parent_layout.addWidget(conn_group)
    
    def create_tabbed_interface(self, parent_layout):
        """Create tabbed chat interface"""
        self.tab_widget = QTabWidget()
        
        # Public chat tab
        public_tab = QWidget()
        public_layout = QVBoxLayout(public_tab)
        
        self.public_chat_display = QTextEdit()
        self.public_chat_display.setReadOnly(True)
        self.public_chat_display.setFont(QFont("Arial", 11))
        public_layout.addWidget(self.public_chat_display)
        
        self.tab_widget.addTab(public_tab, "Public Chat")
        
        # Group chats tab
        group_tab = QWidget()
        group_layout = QVBoxLayout(group_tab)
        
        self.group_chat_display = QTextEdit()
        self.group_chat_display.setReadOnly(True)
        self.group_chat_display.setFont(QFont("Arial", 11))
        group_layout.addWidget(self.group_chat_display)
        
        self.tab_widget.addTab(group_tab, "Group Chats")
        
        # Private chats tab
        private_tab = QWidget()
        private_layout = QVBoxLayout(private_tab)
        
        self.private_chat_display = QTextEdit()
        self.private_chat_display.setReadOnly(True)
        self.private_chat_display.setFont(QFont("Arial", 11))
        private_layout.addWidget(self.private_chat_display)
        
        self.tab_widget.addTab(private_tab, "Private Chats")
        
        parent_layout.addWidget(self.tab_widget)
    
    def create_message_input_frame(self, parent_layout):
        """Create message input area"""
        input_group = QGroupBox("Send Message")
        input_layout = QVBoxLayout(input_group)
        
        # Message type selector
        type_layout = QHBoxLayout()
        
        self.msg_type_label = QLabel("Public message")
        type_layout.addWidget(self.msg_type_label)
        type_layout.addStretch()
        
        input_layout.addLayout(type_layout)
        
        # Message input
        msg_input_layout = QHBoxLayout()
        
        self.message_entry = QLineEdit()
        self.message_entry.setFont(QFont("Arial", 12))
        self.message_entry.setEnabled(False)
        self.message_entry.returnPressed.connect(self.send_message)
        self.message_entry.setPlaceholderText("Type your message here... Use @user for private, #group for group")
        self.message_entry.textChanged.connect(self.update_message_type_indicator)
        msg_input_layout.addWidget(self.message_entry)
        
        # Send button
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setEnabled(False)
        self.send_btn.setFixedWidth(80)
        msg_input_layout.addWidget(self.send_btn)
        
        input_layout.addLayout(msg_input_layout)
        parent_layout.addWidget(input_group)
    
    def create_commands_frame(self, parent_layout):
        """Create commands information"""
        cmd_label = QLabel("""Commands: @username message (private) | #groupname message (group) | /users (online users) | 
/creategroup name | /addtogroup name user | /leavegroup name | /listgroups | /quit""")
        cmd_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        cmd_label.setAlignment(Qt.AlignCenter)
        cmd_label.setWordWrap(True)
        parent_layout.addWidget(cmd_label)
    
    def update_message_type_indicator(self):
        """Update message type indicator based on input"""
        text = self.message_entry.text()
        if text.startswith('@'):
            self.msg_type_label.setText("Private message")
            self.msg_type_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        elif text.startswith('#'):
            self.msg_type_label.setText("Group message")
            self.msg_type_label.setStyleSheet("color: #3498db; font-weight: bold;")
        elif text.startswith('/'):
            self.msg_type_label.setText("Command")
            self.msg_type_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        else:
            self.msg_type_label.setText("Public message")
            self.msg_type_label.setStyleSheet("color: #27ae60; font-weight: bold;")
    
    def open_group_management(self):
        """Open group management dialog"""
        if self.connected:
            dialog = GroupManagementDialog(self, self)
            dialog.exec_()
    
    def send_command(self, command):
        """Send command to server"""
        if self.connected and self.socket:
            try:
                self.socket.send(command.encode('utf-8'))
            except Exception as e:
                QMessageBox.critical(self, "Command Error", f"Could not send command:\n{str(e)}")
    
    def apply_whatsapp_style(self):
        """Apply WhatsApp-like styling"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #075E54;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #34495e;
                border-radius: 10px;
                margin-top: 10px;
                background-color: #ecf0f1;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
                font-size: 12px;
            }
            
            QTextEdit {
                background-color: #ECE5DD;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 8px;
                color: #2c3e50;
                selection-background-color: #34B7F1;
            }
            
            QLineEdit {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
                color: #2c3e50;
            }
            
            QLineEdit:focus {
                border-color: #25D366;
            }
            
            QPushButton {
                background-color: #25D366;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                font-size: 11px;
            }
            
            QPushButton:hover {
                background-color: #20bd5a;
            }
            
            QPushButton:pressed {
                background-color: #1da851;
            }
            
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
            }
            
            QPushButton#disconnect_btn {
                background-color: #e74c3c;
            }
            
            QPushButton#disconnect_btn:hover {
                background-color: #c0392b;
            }
            
            QLabel {
                color: #2c3e50;
                font-weight: bold;
            }
            
            QStatusBar {
                background-color: #34495e;
                color: white;
                border-top: 1px solid #2c3e50;
            }
            
            QTabWidget::pane {
                border: 2px solid #34495e;
                border-radius: 8px;
                background-color: #ecf0f1;
            }
            
            QTabWidget::tab-bar {
                alignment: center;
            }
            
            QTabBar::tab {
                background-color: #bdc3c7;
                border: 1px solid #34495e;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            
            QTabBar::tab:selected {
                background-color: #25D366;
                color: white;
                font-weight: bold;
            }
            
            QTabBar::tab:hover {
                background-color: #95a5a6;
            }
        """)
        
        # Set specific button styles
        self.disconnect_btn.setObjectName("disconnect_btn")
    
    def display_message(self, message: str, is_history=False, message_type="public"):
        """Display message in appropriate chat area"""
        # Determine which display to use
        if message_type == "group" or "[" in message and "]" in message.split(":")[0]:
            display = self.group_chat_display
        elif "[Private]" in message or "[Private to" in message:
            display = self.private_chat_display
        else:
            display = self.public_chat_display
        
        if is_history:
            # Style history messages differently
            display.append(f'<span style="color: #7f8c8d; font-style: italic;">{message}</span>')
        else:
            # Check message type and style accordingly
            if "[Private]" in message:
                display.append(f'<span style="color: #e74c3c; font-weight: bold;">{message}</span>')
            elif "[Private to" in message:
                display.append(f'<span style="color: #8e44ad; font-weight: bold;">{message}</span>')
            elif message.startswith('[') and ']' in message:
                # Group message
                display.append(f'<span style="color: #3498db; font-weight: bold;">{message}</span>')
            elif "joined the chat" in message or "left the chat" in message:
                display.append(f'<span style="color: #f39c12; font-style: italic;">{message}</span>')
            else:
                display.append(f'<span style="color: #2c3e50;">{message}</span>')
        
        # Auto-scroll to bottom
        scrollbar = display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def connect_to_server(self):
        """Connect to chat server"""
        try:
            host = self.host_entry.text() or "localhost"
            port = int(self.port_entry.text() or "12345")
            
            # Get username
            username, ok = QInputDialog.getText(self, 'Username', 'Enter your username:')
            if not ok or not username.strip():
                return
            
            self.username = username.strip()
            
            # Create socket and connect
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            
            # Handle initial server communication
            welcome_prompt = self.socket.recv(1024).decode('utf-8')
            if "Enter your username" in welcome_prompt:
                self.socket.send(self.username.encode('utf-8'))
                
                # Check if username was accepted
                response = self.socket.recv(1024).decode('utf-8')
                if "already taken" in response:
                    QMessageBox.critical(self, "Error", "Username already taken!")
                    self.socket.close()
                    return
                else:
                    self.display_message(response)
            
            self.connected = True
            self.update_ui_state()
            
            # Start message receiver thread
            self.message_receiver = MessageReceiver(self.socket)
            self.message_receiver.message_received.connect(self.on_message_received)
            self.message_receiver.connection_lost.connect(self.on_connection_lost)
            self.message_receiver.start()
            
            self.display_message(f"Connected as {self.username} to {host}:{port}")
            self.load_chat_history()
            
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Could not connect to server:\n{str(e)}")
    
    def disconnect(self):
        """Disconnect from server"""
        if self.connected and self.socket:
            try:
                self.socket.send("/quit".encode('utf-8'))
            except:
                pass
            
            if self.message_receiver:
                self.message_receiver.stop()
                self.message_receiver.wait()
            
            try:
                self.socket.close()
            except:
                pass
        
        self.connected = False
        self.socket = None
        self.message_receiver = None
        self.update_ui_state()
        self.display_message("Disconnected from server")
    
    def update_ui_state(self):
        """Update UI based on connection state"""
        if self.connected:
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.message_entry.setEnabled(True)
            self.send_btn.setEnabled(True)
            self.group_mgmt_btn.setEnabled(True)
            self.status_bar.showMessage(f"Connected as {self.username}")
            self.message_entry.setFocus()
        else:
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.message_entry.setEnabled(False)
            self.send_btn.setEnabled(False)
            self.group_mgmt_btn.setEnabled(False)
            self.status_bar.showMessage("Not connected")
    
    def send_message(self):
        """Send message to server"""
        if not self.connected or not self.socket:
            return
        
        message = self.message_entry.text().strip()
        if not message:
            return
        
        try:
            self.socket.send(message.encode('utf-8'))
            
            # Save to local history
            if message.startswith('@'):
                # Private message
                parts = message[1:].split(' ', 1)
                if len(parts) >= 2:
                    target_user, private_msg = parts
                    self.save_chat_history(self.username, target_user, private_msg, "direct")
            elif message.startswith('#'):
                # Group message
                parts = message[1:].split(' ', 1)
                if len(parts) >= 2:
                    group_name, group_msg = parts
                    self.save_chat_history(self.username, group_name, group_msg, "group")
            elif not message.startswith('/'):
                # Public message
                self.save_chat_history(self.username, "Public", message, "direct")
            
            self.message_entry.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "Send Error", f"Could not send message:\n{str(e)}")
    
    def on_message_received(self, message):
        """Handle received message"""
        # Parse and save received messages
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        display_msg = f"[{timestamp}] {message}"
        
        # Determine message type and save to history
        message_type = "public"
        
        if message.startswith('[') and ']' in message and not message.startswith('[Private'):
            # Group message
            group_name = message.split(']')[0][1:]
            sender = message.split('] ')[1].split(':')[0] if ':' in message else "System"
            if ':' in message:
                msg_content = ':'.join(message.split(': ')[1:])
                self.save_chat_history(sender, group_name, msg_content, "group")
            message_type = "group"
        elif message.startswith('[Private]'):
            # Private message received
            sender = message.split('] ')[1].split(':')[0]
            msg_content = ':'.join(message.split(': ')[1:])
            self.save_chat_history(sender, self.username, msg_content, "direct")
            message_type = "private"
        elif not message.startswith('[Private to') and ':' in message and not message.endswith('the chat'):
            # Public message
            sender = message.split(':')[0]
            msg_content = ':'.join(message.split(':')[1:]).strip()
            self.save_chat_history(sender, "Public", msg_content, "direct")
            message_type = "public"
        
        self.display_message(display_msg, message_type=message_type)
    
    def on_connection_lost(self):
        """Handle connection lost"""
        if self.connected:
            QMessageBox.warning(self, "Connection Lost", "Connection to server was lost.")
            self.disconnect()
    
    def closeEvent(self, event):
        """Handle window closing"""
        if self.connected:
            self.disconnect()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("WhatsApp-like Chat with Groups")
    app.setOrganizationName("ChatApp")
    
    # Create and show main window
    window = ChatClientGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()