from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import json
import getpass
import re
import time
import sys

class SecureOfflineSeedStorage:
    VERSION = "1.0"
    AUTHOR = "Asipaka CJE"
    SOCIAL = "@kn0treel"
    DATA_FILE = "soss_wallets.dat"
    
    def __init__(self):
        self.wallets = self.load_wallet_index()
    
    def display_banner(self):
        """Display the application banner."""
        print("\n######## *** SOSS v{} *** ########".format(self.VERSION))
        print("Secure Offline Seed Storage")
        print("Your crypto seed phrases, securely encrypted and stored offline.")
        print("Author : {}".format(self.AUTHOR))
        print("x: {}".format(self.SOCIAL))
        print("######## ------------------- ########\n")
    
    def load_wallet_index(self):
        """Load the wallet index from the data file."""
        try:
            if os.path.exists(self.DATA_FILE):
                with open(self.DATA_FILE, "rb") as f:
                    encrypted_data = f.read()
                    if not encrypted_data:
                        return {}
                    
                    # We'll use a fixed salt for the index file
                    # In a production environment, consider a more secure approach
                    salt = encrypted_data[:16]
                    encrypted_index = encrypted_data[16:]
                    
                    # Ask for master password to decrypt wallet index
                    master_pass = self.get_password("Enter master password to access wallets: ")
                    
                    try:
                        key = self.derive_key(master_pass.encode(), salt)
                        fernet = Fernet(key)
                        decrypted_data = fernet.decrypt(encrypted_index).decode()
                        return json.loads(decrypted_data)
                    except Exception:
                        print("Invalid password or corrupted data file.")
                        return {}
            return {}
        except Exception as e:
            print(f"Error loading wallet index: {e}")
            return {}
    
    def save_wallet_index(self):
        """Save the wallet index to the data file."""
        try:
            if not self.wallets:
                return
                
            # Create or get master password
            if not os.path.exists(self.DATA_FILE):
                print("\nYou need to create a master password to protect your wallet index.")
                print("This password will be used to access your list of wallets.")
                master_pass = self.get_new_password()
            else:
                master_pass = self.get_password("Enter master password to update wallet index: ")
            
            # Encrypt the wallet index
            salt = os.urandom(16)
            wallet_data = json.dumps(self.wallets).encode()
            
            key = self.derive_key(master_pass.encode(), salt)
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(wallet_data)
            
            with open(self.DATA_FILE, "wb") as f:
                f.write(salt + encrypted_data)
                
            print("\nWallet index updated successfully.")
        except Exception as e:
            print(f"Error saving wallet index: {e}")
    
    def derive_key(self, passphrase, salt):
        """Derive encryption key from passphrase and salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(passphrase))
        return key
    
    def get_password(self, prompt="Enter passphrase: "):
        """Get password securely (hidden input)."""
        return getpass.getpass(prompt)
    
    def get_new_password(self):
        """Get a new password with confirmation and validation."""
        while True:
            password = self.get_password("Enter new passphrase: ")
            
            # Validate password complexity
            if not self.validate_password(password):
                print("Password must be at least 8 characters and include uppercase, lowercase letters, and numbers.")
                continue
                
            confirm_password = self.get_password("Confirm passphrase: ")
            
            if password != confirm_password:
                print("Passphrases do not match. Please try again.")
                continue
                
            return password
    
    def validate_password(self, password):
        """Validate password complexity."""
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'[0-9]', password):
            return False
        return True
    
    def validate_seed_phrase(self, seed_phrase):
        """Validate that the seed phrase has the correct number of words."""
        words = seed_phrase.strip().split()
        valid_lengths = [12, 18, 24]
        
        if len(words) not in valid_lengths:
            return False, len(words)
        
        return True, len(words)
    
    def encrypt_seed(self):
        """Encrypt a seed phrase and save it."""
        # Get wallet name
        while True:
            wallet_name = input("Enter a name for this wallet: ").strip()
            if not wallet_name:
                print("Wallet name cannot be empty.")
                continue
                
            if wallet_name in self.wallets:
                overwrite = input(f"Wallet '{wallet_name}' already exists. Overwrite? (y/n): ").lower()
                if overwrite != 'y':
                    continue
            
            break
            
        # Get seed phrase with validation
        while True:
            seed = input("Enter your 12, 18, or 24-word seed phrase, separated by spaces: ").strip()
            valid, word_count = self.validate_seed_phrase(seed)
            
            if not valid:
                print(f"Error: Seed phrase has {word_count} words. It must be 12, 18, or 24 words.")
                continue
                
            break
            
        # Normalize seed phrase
        seed = " ".join(seed.strip().split()).encode()
        
        # Get passphrase with confirmation
        passphrase = self.get_new_password()
        
        # Generate salt and encrypt
        salt = os.urandom(16)
        key = self.derive_key(passphrase.encode(), salt)
        fernet = Fernet(key)
        encrypted_seed = fernet.encrypt(seed)
        
        # Save encrypted seed
        file_name = f"{wallet_name.replace(' ', '_')}.seed"
        with open(file_name, "wb") as f:
            f.write(salt + encrypted_seed)
            
        # Update wallet index
        self.wallets[wallet_name] = {
            "file": file_name,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "word_count": word_count
        }
        
        self.save_wallet_index()
        
        print(f"\nSeed encrypted and saved as '{file_name}' locally.")
        print("Move this file to your flash drive when ready!")
    
    def decrypt_seed(self):
        """Decrypt a seed phrase."""
        if not self.wallets:
            print("No wallets found. Please create a wallet first.")
            return
            
        # List available wallets
        print("\nAvailable wallets:")
        for idx, (name, info) in enumerate(self.wallets.items(), 1):
            print(f"{idx}. {name} ({info['word_count']} words) - Created: {info['created']}")
            
        # Get wallet selection
        while True:
            try:
                selection = input("\nEnter wallet number or name (or 'q' to quit): ")
                if selection.lower() == 'q':
                    return
                    
                wallet_name = None
                if selection.isdigit():
                    idx = int(selection)
                    if 1 <= idx <= len(self.wallets):
                        wallet_name = list(self.wallets.keys())[idx-1]
                elif selection in self.wallets:
                    wallet_name = selection
                    
                if wallet_name:
                    break
                    
                print("Invalid selection. Please try again.")
            except Exception:
                print("Invalid input. Please try again.")
        
        # Get file path
        file_path = self.wallets[wallet_name]["file"]
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found.")
            
            # Ask if they want to update the path
            new_path = input("Enter the correct file path (or press Enter to cancel): ")
            if not new_path or not os.path.exists(new_path):
                print("Operation cancelled.")
                return
                
            file_path = new_path
            self.wallets[wallet_name]["file"] = file_path
            self.save_wallet_index()
        
        # Read the encrypted file
        try:
            with open(file_path, "rb") as f:
                data = f.read()
                salt = data[:16]
                encrypted_seed = data[16:]
        except Exception as e:
            print(f"Error reading file: {e}")
            return
            
        # Get passphrase
        passphrase = self.get_password(f"Enter passphrase for '{wallet_name}': ")
        
        # Derive key and decrypt
        try:
            key = self.derive_key(passphrase.encode(), salt)
            fernet = Fernet(key)
            
            # Decrypt with delay for security theater
            print("Verifying data integrity...", end="", flush=True)
            for _ in range(5):  # 5-second delay
                time.sleep(1)
                print(".", end="", flush=True)
                
            seed = fernet.decrypt(encrypted_seed).decode()
            
            print("\n\nAccess granted.")
            print(f"Wallet: {wallet_name}")
            print("Your seed phrase:", seed)
            print("\n[SOSS] Protecting your wealth securely, offline.")
            
            # Auto-hide after a timeout
            print("\nThis screen will clear in 30 seconds. Press Ctrl+C to clear immediately.")
            try:
                time.sleep(30)
            except KeyboardInterrupt:
                pass
                
            # Clear screen
            os.system('cls' if os.name == 'nt' else 'clear')
            
        except Exception:
            print("\nWrong passphrase or corrupted data.")
    
    def list_wallets(self):
        """List all saved wallets."""
        if not self.wallets:
            print("No wallets found.")
            return
            
        print("\nSaved wallets:")
        for name, info in self.wallets.items():
            print(f"- {name} ({info['word_count']} words)")
            print(f"  File: {info['file']}")
            print(f"  Created: {info['created']}")
            print()
    
    def main_menu(self):
        """Display the main menu and handle user input."""
        while True:
            print("\n########## ********* ##########")
            print("\nSecure Offline Seed Storage - Main Menu")
            print("\n#################################\n")
            print("1. Create new encrypted wallet")
            print("2. Access existing wallet")
            print("3. List saved wallets")
            print("4. Exit")
            print("\n########## ********* ##########")
            
            choice = input("\nEnter your choice (1-4): ")
            
            if choice == '1':
                self.encrypt_seed()
            elif choice == '2':
                self.decrypt_seed()
            elif choice == '3':
                self.list_wallets()
            elif choice == '4':
                print("\n**********************************************************")
                print("Exiting SOSS. Your crypto, your keys, your responsibility.")
                print("**********************************************************")
                break
            else:
                print("Invalid choice. Please try again.")
    
    def run(self):
        """Run the application."""
        self.display_banner()
        self.main_menu()


if __name__ == "__main__":
    app = SecureOfflineSeedStorage()
    app.run()