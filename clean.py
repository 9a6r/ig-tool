import sys
import os
import time
import random
import urllib.parse
from instagrapi import Client

class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

SESSION_FILE = "session.txt"

def banner():
    print(f"\n{Colors.BLUE}")
    print("="*45)
    print("   Instagram DM Cleaner Tool")
    print("="*45 + f"{Colors.ENDC}")

def load_or_request_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            session_id = f.read().strip()
            if session_id:
                print(f"{Colors.BLUE}[*] Found saved session in {SESSION_FILE}{Colors.ENDC}")
                return session_id
                
    print(f"{Colors.WARNING}[!] No saved session found.{Colors.ENDC}")
    session_id = input(f"{Colors.BOLD}Paste your Session ID here: {Colors.ENDC}").strip()
    
    if session_id:
        with open(SESSION_FILE, "w") as f:
            f.write(session_id)
        print(f"{Colors.GREEN}[+] Session saved to {SESSION_FILE} for future use.{Colors.ENDC}")
        return session_id
    else:
        print(f"{Colors.FAIL}[!] Session ID cannot be empty.{Colors.ENDC}")
        sys.exit()

def process_session(session_id):
    cl = Client()
    try:
        decoded_session = urllib.parse.unquote(session_id)
        cl.login_by_sessionid(decoded_session)
        return cl
    except Exception as e:
        print(f"{Colors.FAIL}[!] Invalid or expired session: {e}{Colors.ENDC}")
        return None

def delete_messages(cl, chat_id, delay_choice):
    my_user_id = str(cl.user_id)
    print(f"\n{Colors.BLUE}[*] Starting cleanup for Chat ID: {chat_id}{Colors.ENDC}")
    
    cursor = None
    deleted_total = 0
    page_num = 1
    
    while True:
        try:
            print(f"[-] Fetching page {page_num}...")
            
            params = {"visual_message_return_type": "unseen"}
            if cursor:
                params["cursor"] = cursor
                
            res = cl.private_request(f"direct_v2/threads/{chat_id}/", params=params)
            
            thread_data = res.get("thread", {})
            messages = thread_data.get("items", [])
            
            if not messages:
                break
                
            my_messages = [msg for msg in messages if str(msg.get("user_id")) == my_user_id]
            
            if my_messages:
                print(f"[-] Found {len(my_messages)} message(s) for you in this page. Deleting...")
                for msg in my_messages:
                    msg_id = msg.get("item_id")
                    try:
                        cl.direct_message_unsend(chat_id, msg_id)
                        deleted_total += 1
                        
                        if delay_choice == 'r':
                            sleep_time = random.randint(3, 6)
                        else:
                            sleep_time = delay_choice
                            
                        print(f"    -> Deleted (Total: {deleted_total}) | Waiting {sleep_time}s...")
                        time.sleep(sleep_time)
                        
                    except Exception as e:
                        print(f"{Colors.FAIL}    [X] Failed to delete message: {e}{Colors.ENDC}")
                        time.sleep(5)
            else:
                print("[-] No messages from you in this page. Going deeper...")
                
            cursor = thread_data.get("oldest_cursor")
            
            if not cursor:
                print(f"\n{Colors.GREEN}[+] Reached the beginning of the chat.{Colors.ENDC}")
                break
                
            page_num += 1
            time.sleep(1) # التعديل هنا: خليناها ثانية واحدة بدل ثانيتين
            
        except Exception as e:
            print(f"{Colors.FAIL}[!] Error fetching page: {e}{Colors.ENDC}")
            time.sleep(10)
            
    print(f"\n{Colors.GREEN}[+] Cleanup Complete! Total deleted: {deleted_total} messages.{Colors.ENDC}")

def main():
    banner()
    
    session_id = load_or_request_session()
    print(f"{Colors.BLUE}[*] Validating session...{Colors.ENDC}")
    
    cl = process_session(session_id)
    if not cl:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        sys.exit()
        
    print(f"{Colors.GREEN}[+] Session Valid! Logged in successfully.{Colors.ENDC}")
    
    while True:
        print(f"\n{Colors.BOLD}--- Main Menu ---{Colors.ENDC}")
        print("1 - List Conversations")
        print("2 - Delete Messages (Chat ID required)")
        print("3 - Exit")
        
        choice = input("\nSelect: ").strip()
        
        if choice == "1":
            print(f"\n{Colors.BLUE}[*] Fetching recent conversations...{Colors.ENDC}")
            try:
                threads = cl.direct_threads(amount=15)
                for t in threads:
                    title = getattr(t, 'thread_title', '')
                    if not title:
                        users = getattr(t, 'users', [])
                        title = ", ".join([getattr(u, 'username', 'Unknown') for u in users])
                    
                    name = title or "Unknown Chat"
                    print(f"[{Colors.GREEN}{t.id}{Colors.ENDC}] -> {name}")
            except Exception as e:
                print(f"{Colors.FAIL}[!] Error fetching threads: {e}{Colors.ENDC}")
                
        elif choice == "2":
            chat_id = input("Enter Chat ID: ").strip()
            if chat_id:
                delay_input = input("Enter delay in seconds (e.g. 2.5) or 'r' for random (3-6s): ").strip().lower()
                
                if delay_input == 'r':
                    delay_choice = 'r'
                else:
                    try:
                        delay_choice = float(delay_input)
                    except ValueError:
                        print(f"{Colors.WARNING}[!] Invalid input. Defaulting to random (3-6s).{Colors.ENDC}")
                        delay_choice = 'r'
                        
                delete_messages(cl, chat_id, delay_choice)
            else:
                print(f"{Colors.WARNING}[!] Chat ID cannot be empty.{Colors.ENDC}")
                
        elif choice == "3":
            print("Exiting...")
            sys.exit()
        else:
            print(f"{Colors.WARNING}[!] Invalid choice.{Colors.ENDC}")

if __name__ == "__main__":
    main()
