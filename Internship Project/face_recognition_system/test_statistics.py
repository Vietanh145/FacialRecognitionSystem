#!/usr/bin/env python3
"""
Demo script to test detailed statistics feature in Admin UI
"""

import tkinter as tk
from src.admin_interface import AdminInterface

def main():
    """Run Admin UI demo with detailed statistics feature"""
    root = tk.Tk()
    
    # Set up application style
    style = tk.ttk.Style()
    style.theme_use('clam')
    
    # Start Admin Interface
    AdminInterface.start(root)
    
    # Run main loop
    root.mainloop()

if __name__ == "__main__":
    main() 