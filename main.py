import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

def pad(data): return data + b' ' * (16 - len(data) % 16)
def unpad(data): return data.rstrip(b' ')

def encrypt(data, password):
    key = password.encode().ljust(32, b'\0')
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(data.encode()))
    return base64.b64encode(iv + encrypted)

def decrypt(enc_data, password):
    key = password.encode().ljust(32, b'\0')
    try:
        raw = base64.b64decode(enc_data)
        iv = raw[:16]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(raw[16:])
        return unpad(decrypted).decode()
    except:
        return None

def embed_to_image(image_path, encrypted_data):
    with open(image_path, 'ab') as f:
        f.write(b'\n###DATA###\n')
        f.write(encrypted_data)

def extract_from_image(image_path):
    with open(image_path, 'rb') as f:
        content = f.read()
        if b'###DATA###' in content:
            return content.split(b'###DATA###')[-1]
        return None

class PasswordManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stego Password Manager")
        self.image_path = ''
        self.password = ''
        self.data = []
        
        self.login_frame()

    def login_frame(self):
        self.clear_root()
        tk.Label(self.root, text="Select Image").pack()
        tk.Button(self.root, text="Browse Image", command=self.browse_image).pack()
        self.img_label = tk.Label(self.root, text="No image selected")
        self.img_label.pack()

        tk.Label(self.root, text="Enter Master Password").pack()
        self.pass_entry = tk.Entry(self.root, show="*")
        self.pass_entry.pack()

        tk.Button(self.root, text="Login", command=self.load_data).pack()

    def browse_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg")])
        if path:
            self.image_path = path
            self.img_label.config(text=os.path.basename(path))

    def load_data(self):
        self.password = self.pass_entry.get()
        raw = extract_from_image(self.image_path)
        if raw:
            decrypted = decrypt(raw, self.password)
            if decrypted:
                self.data = json.loads(decrypted)
            else:
                messagebox.showerror("Error", "Incorrect password or corrupted image.")
                return
        else:
            self.data = []

        self.main_frame()

    def main_frame(self):
        self.clear_root()
        tk.Label(self.root, text="Saved Logins").pack()

        self.entries_frame = tk.Frame(self.root)
        self.entries_frame.pack()

        self.display_entries()

        tk.Button(self.root, text="Add New", command=self.add_entry_dialog).pack(pady=5)
        tk.Button(self.root, text="Save to Image", command=self.save_to_image).pack()

    def display_entries(self):
        for widget in self.entries_frame.winfo_children():
            widget.destroy()

        for entry in self.data:
            txt = f"{entry['app']} | {entry['email']} | {entry['password']}"
            tk.Label(self.entries_frame, text=txt).pack(anchor='w')

    def add_entry_dialog(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add Entry")

        tk.Label(popup, text="App Name").pack()
        app_entry = tk.Entry(popup)
        app_entry.pack()

        tk.Label(popup, text="Email/Username").pack()
        email_entry = tk.Entry(popup)
        email_entry.pack()

        tk.Label(popup, text="Password").pack()
        pass_entry = tk.Entry(popup)
        pass_entry.pack()

        def save():
            self.data.append({
                'app': app_entry.get(),
                'email': email_entry.get(),
                'password': pass_entry.get()
            })
            popup.destroy()
            self.display_entries()

        tk.Button(popup, text="Save", command=save).pack()

    def save_to_image(self):
        json_data = json.dumps(self.data)
        encrypted = encrypt(json_data, self.password)

        # Read the original image content up to where the data might be
        original_content = b''
        try:
            with open(self.image_path, 'rb') as f:
                content_before_data = f.read().split(b'###DATA###')[0]
                original_content = content_before_data
        except FileNotFoundError:
            messagebox.showerror("Error", "Original image not found!")
            return

        # Overwrite the original image
        with open(self.image_path, 'wb') as f:
            f.write(original_content) # Write the original image data without the old embedded data
            f.write(b'\n###DATA###\n')
            f.write(encrypted)
        messagebox.showinfo("Saved", f"Data saved to: {self.image_path}")

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordManagerApp(root)
    root.mainloop()
