import tkinter as tk
from tkinter import filedialog

# Create main window
root = tk.Tk()
root.title("AI Pokémon Grader App")
root.geometry("1440x960")
root.configure(bg="#212b31")  # dark background

# Title label (less padding now)
title = tk.Label(root, text="AI Pokémon Grader", font=("Segoe UI", 20, "bold"),
                 bg="#212b31", fg="#cad2c5")
title.pack(pady=(10, 10))  # reduced vertical space

# Main frame
frame = tk.Frame(root, bg="#353F47")
frame.pack(padx=10, pady=(5, 10), fill="both", expand=True)  # tighter top spacing

# Instruction label
label = tk.Label(frame, text="Select an image to upload:", font=("Segoe UI", 12),
                 bg="#353F47", fg="#d8e2dc")
label.pack(pady=(10, 6))

# --- File selector area ---
selected_file = tk.StringVar(value="No file selected")

def browse_file():
    file_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All Files", "*.*")]
    )
    if file_path:
        selected_file.set(file_path)

# Reusable rectangular button builder
def rect_button(parent, text, command=None, width=140, height=40,
                bg="#2b363c", fg="#cad2c5", outline="#3f4e55", hover="#3c4a50"):
    c = tk.Canvas(parent, width=width, height=height, bg=parent["bg"],
                  highlightthickness=0, bd=0)
    c.pack_propagate(False)
    rect_id = c.create_rectangle(2, 2, width-2, height-2, fill=bg, outline=outline, width=1)
    text_id = c.create_text(width/2, height/2, text=text, fill=fg,
                            font=("Segoe UI", 10, "bold"))

    def on_enter(_): c.itemconfig(rect_id, fill=hover)
    def on_leave(_): c.itemconfig(rect_id, fill=bg)
    c.bind("<Enter>", on_enter)
    c.bind("<Leave>", on_leave)

    if command:
        c.bind("<Button-1>", lambda _: command())
    return c

# File selection row
file_frame = tk.Frame(frame, bg="#353F47")
file_frame.pack(pady=8)

browse_btn = rect_button(file_frame, "Browse Files", command=browse_file, width=150, height=36)
browse_btn.pack(side="left", padx=(0, 10))

file_label = tk.Label(file_frame, textvariable=selected_file, bg="#353F47",
                      fg="#cad2c5", font=("Segoe UI", 10), anchor="w")
file_label.pack(side="left", padx=5)

# Submit button
def on_submit():
    print("Selected file:", selected_file.get())

submit_canvas = rect_button(frame, "Submit", command=on_submit, width=120, height=36,
                            bg="#2b363c", fg="#cad2c5", outline="#4a595f", hover="#3c4a50")
submit_canvas.pack(pady=10)

# Bottom buttons frame
bottom_frame = tk.Frame(frame, bg="#353F47")
bottom_frame.pack(side="bottom", anchor="w", padx=30, pady=25)

# Bottom-left buttons
settings_btn = rect_button(bottom_frame, "Settings / Help", width=180, height=48,
                           bg="#2b363c", fg="#cad2c5", outline="#4a595f", hover="#3c4a50")
settings_btn.pack(side="left", padx=(0, 12))

howitworks_btn = rect_button(bottom_frame, "How it works", width=180, height=48,
                             bg="#2b363c", fg="#cad2c5", outline="#4a595f", hover="#3c4a50")
howitworks_btn.pack(side="left")

# Footer
footer = tk.Label(root, text="© 2025 Logan Edwards", font=("Segoe UI", 9),
                  bg="#212b31", fg="#84a98c")
footer.pack(side="bottom", pady=10)

# Run app
root.mainloop()
