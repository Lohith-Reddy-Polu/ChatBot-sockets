#!/usr/bin/env python3
"""
Chat Viewer Utility
View entire chat history between two users or group chats

Usage:
    python chat_viewer.py --users user1 user2
    python chat_viewer.py --group groupname
    python chat_viewer.py --list-chats
    python chat_viewer.py --list-groups
"""

import json
import os
import argparse
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

class ChatViewer:
    def __init__(self):
        self.server_logs_dir = "server_logs"
        self.client_logs_dir = "client_logs"
        self.group_logs_dir = os.path.join(self.server_logs_dir, "groups")
    
    def verify_message_integrity(self, message_data: Dict) -> bool:
        """Verify message integrity using stored hash"""
        try:
            original_hash = message_data.get('message_hash', '')
            current_hash = hashlib.sha256(message_data['message'].encode()).hexdigest()
            return original_hash == current_hash
        except:
            return False
    
    def format_message(self, msg_data: Dict, show_hash: bool = False) -> str:
        """Format message for display"""
        timestamp = msg_data.get('timestamp', 'Unknown time')
        sender = msg_data.get('sender', 'Unknown')
        receiver = msg_data.get('receiver', 'Unknown')
        message = msg_data.get('message', '')
        msg_type = msg_data.get('type', 'direct')
        
        # Verify integrity
        integrity = "✓" if self.verify_message_integrity(msg_data) else "⚠"
        
        if msg_type == "group":
            formatted = f"[{timestamp}] {integrity} {sender} → [{receiver}]: {message}"
        else:
            formatted = f"[{timestamp}] {integrity} {sender} → {receiver}: {message}"
        
        if show_hash:
            msg_hash = msg_data.get('message_hash', 'No hash')[:16] + "..."
            formatted += f" (Hash: {msg_hash})"
        
        return formatted
    
    def view_direct_chat(self, user1: str, user2: str, show_hash: bool = False) -> List[str]:
        """View chat history between two users"""
        # Sort usernames to match file naming convention
        participants = sorted([user1, user2])
        filename = f"{participants[0]}_{participants[1]}_conversation.json"
        filepath = os.path.join(self.server_logs_dir, filename)
        
        if not os.path.exists(filepath):
            return [f"❌ No chat history found between {user1} and {user2}"]
        
        try:
            with open(filepath, 'r') as f:
                chat_history = json.load(f)
            
            if not chat_history:
                return [f"📝 Chat history between {user1} and {user2} is empty"]
            
            messages = []
            messages.append(f"💬 Chat History: {user1} ↔ {user2}")
            messages.append(f"📅 Total messages: {len(chat_history)}")
            messages.append("=" * 80)
            
            for msg_data in chat_history:
                messages.append(self.format_message(msg_data, show_hash))
            
            messages.append("=" * 80)
            messages.append(f"✅ End of chat history ({len(chat_history)} messages)")
            
            return messages
            
        except json.JSONDecodeError:
            return [f"❌ Error: Chat file is corrupted"]
        except Exception as e:
            return [f"❌ Error reading chat file: {str(e)}"]
    
    def view_group_chat(self, group_name: str, show_hash: bool = False) -> List[str]:
        """View group chat history"""
        filename = f"{group_name}_group.json"
        filepath = os.path.join(self.group_logs_dir, filename)
        
        if not os.path.exists(filepath):
            return [f"❌ No group chat history found for '{group_name}'"]
        
        try:
            with open(filepath, 'r') as f:
                chat_history = json.load(f)
            
            if not chat_history:
                return [f"📝 Group chat history for '{group_name}' is empty"]
            
            # Load group info if available
            group_info_file = os.path.join(self.group_logs_dir, f"{group_name}_info.json")
            group_info = {}
            if os.path.exists(group_info_file):
                with open(group_info_file, 'r') as f:
                    group_info = json.load(f)
            
            messages = []
            messages.append(f"👥 Group Chat History: {group_name}")
            
            if group_info:
                messages.append(f"👑 Admin: {group_info.get('admin', 'Unknown')}")
                messages.append(f"👤 Members: {', '.join(group_info.get('members', []))}")
                messages.append(f"📅 Created: {group_info.get('created_date', 'Unknown')}")
            
            messages.append(f"💬 Total messages: {len(chat_history)}")
            messages.append("=" * 80)
            
            for msg_data in chat_history:
                messages.append(self.format_message(msg_data, show_hash))
            
            messages.append("=" * 80)
            messages.append(f"✅ End of group chat history ({len(chat_history)} messages)")
            
            return messages
            
        except json.JSONDecodeError:
            return [f"❌ Error: Group chat file is corrupted"]
        except Exception as e:
            return [f"❌ Error reading group chat file: {str(e)}"]
    
    def list_available_chats(self) -> List[str]:
        """List all available direct chats"""
        if not os.path.exists(self.server_logs_dir):
            return ["❌ No server logs directory found"]
        
        chat_files = []
        for filename in os.listdir(self.server_logs_dir):
            if filename.endswith('_conversation.json'):
                # Extract usernames from filename
                base_name = filename.replace('_conversation.json', '')
                users = base_name.split('_', 1)
                if len(users) == 2:
                    chat_files.append((users[0], users[1], filename))
        
        if not chat_files:
            return ["📝 No direct chat histories found"]
        
        messages = []
        messages.append("💬 Available Direct Chats:")
        messages.append("=" * 50)
        
        for user1, user2, filename in sorted(chat_files):
            filepath = os.path.join(self.server_logs_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    history = json.load(f)
                    msg_count = len(history)
                    last_msg = history[-1]['timestamp'] if history else "No messages"
                    messages.append(f"👥 {user1} ↔ {user2} ({msg_count} messages, last: {last_msg})")
            except:
                messages.append(f"👥 {user1} ↔ {user2} (Error reading file)")
        
        return messages
    
    def list_available_groups(self) -> List[str]:
        """List all available group chats"""
        if not os.path.exists(self.group_logs_dir):
            return ["❌ No group logs directory found"]
        
        group_files = []
        info_files = {}
        
        # Collect group chat files and info files
        for filename in os.listdir(self.group_logs_dir):
            if filename.endswith('_group.json'):
                group_name = filename.replace('_group.json', '')
                group_files.append(group_name)
            elif filename.endswith('_info.json'):
                group_name = filename.replace('_info.json', '')
                try:
                    with open(os.path.join(self.group_logs_dir, filename), 'r') as f:
                        info_files[group_name] = json.load(f)
                except:
                    info_files[group_name] = {}
        
        if not group_files:
            return ["📝 No group chat histories found"]
        
        messages = []
        messages.append("👥 Available Group Chats:")
        messages.append("=" * 50)
        
        for group_name in sorted(group_files):
            chat_file = os.path.join(self.group_logs_dir, f"{group_name}_group.json")
            try:
                with open(chat_file, 'r') as f:
                    history = json.load(f)
                    msg_count = len(history)
                    last_msg = history[-1]['timestamp'] if history else "No messages"
                
                # Get group info
                info = info_files.get(group_name, {})
                admin = info.get('admin', 'Unknown')
                member_count = len(info.get('members', []))
                
                messages.append(f"🏷️ {group_name} (Admin: {admin}, {member_count} members, {msg_count} messages, last: {last_msg})")
                
            except:
                messages.append(f"🏷️ {group_name} (Error reading file)")
        
        return messages
    
    def export_chat_to_file(self, messages: List[str], output_file: str):
        """Export chat to a text file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for message in messages:
                    f.write(message + '\n')
            print(f"✅ Chat exported to: {output_file}")
        except Exception as e:
            print(f"❌ Error exporting chat: {str(e)}")
    
    def search_messages(self, search_term: str, chat_type: str = "all") -> List[str]:
        """Search for messages containing specific term"""
        results = []
        results.append(f"🔍 Search Results for: '{search_term}'")
        results.append("=" * 60)
        
        found_count = 0
        
        # Search direct chats
        if chat_type in ["all", "direct"]:
            if os.path.exists(self.server_logs_dir):
                for filename in os.listdir(self.server_logs_dir):
                    if filename.endswith('_conversation.json'):
                        filepath = os.path.join(self.server_logs_dir, filename)
                        try:
                            with open(filepath, 'r') as f:
                                history = json.load(f)
                                for msg in history:
                                    if search_term.lower() in msg.get('message', '').lower():
                                        chat_name = filename.replace('_conversation.json', '').replace('_', ' ↔ ')
                                        results.append(f"💬 {chat_name}")
                                        results.append(f"   {self.format_message(msg)}")
                                        found_count += 1
                        except:
                            continue
        
        # Search group chats
        if chat_type in ["all", "group"]:
            if os.path.exists(self.group_logs_dir):
                for filename in os.listdir(self.group_logs_dir):
                    if filename.endswith('_group.json'):
                        filepath = os.path.join(self.group_logs_dir, filename)
                        try:
                            with open(filepath, 'r') as f:
                                history = json.load(f)
                                for msg in history:
                                    if search_term.lower() in msg.get('message', '').lower():
                                        group_name = filename.replace('_group.json', '')
                                        results.append(f"👥 Group: {group_name}")
                                        results.append(f"   {self.format_message(msg)}")
                                        found_count += 1
                        except:
                            continue
        
        results.append("=" * 60)
        results.append(f"📊 Found {found_count} messages containing '{search_term}'")
        
        return results

def main():
    parser = argparse.ArgumentParser(description="Chat Viewer - View chat histories")
    
    # Main command options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--users', nargs=2, metavar=('USER1', 'USER2'),
                       help='View chat between two users')
    group.add_argument('--group', metavar='GROUPNAME',
                       help='View group chat history')
    group.add_argument('--list-chats', action='store_true',
                       help='List all available direct chats')
    group.add_argument('--list-groups', action='store_true',
                       help='List all available group chats')
    group.add_argument('--search', metavar='TERM',
                       help='Search for messages containing specific term')
    
    # Optional arguments
    parser.add_argument('--show-hash', action='store_true',
                       help='Show message hashes for verification')
    parser.add_argument('--export', metavar='FILENAME',
                       help='Export chat to text file')
    parser.add_argument('--search-type', choices=['all', 'direct', 'group'], 
                       default='all', help='Limit search to specific chat type')
    
    args = parser.parse_args()
    
    viewer = ChatViewer()
    messages = []
    
    try:
        if args.users:
            user1, user2 = args.users
            messages = viewer.view_direct_chat(user1, user2, args.show_hash)
            
        elif args.group:
            messages = viewer.view_group_chat(args.group, args.show_hash)
            
        elif args.list_chats:
            messages = viewer.list_available_chats()
            
        elif args.list_groups:
            messages = viewer.list_available_groups()
            
        elif args.search:
            messages = viewer.search_messages(args.search, args.search_type)
        
        # Display messages
        for message in messages:
            print(message)
        
        # Export if requested
        if args.export:
            viewer.export_chat_to_file(messages, args.export)
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()