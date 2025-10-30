import tkinter as tk
from tkinter import filedialog

# ---------- Reusable Rectangular Button ----------
def rect_button(parent, text, command=None, width=140, height=40,
                bg="#2b363c", fg="#cad2c5", outline="#4a595f", hover="#3c4a50"):
    """Creates a flat rectangular button on a canvas with hover effect and visible border."""
    c = tk.Canvas(parent, width=width, height=height, bg=parent["bg"],
                  highlightthickness=0, bd=0)
    c.pack_propagate(False)
    rect_id = c.create_rectangle(2, 2, width-2, height-2, fill=bg, outline=outline, width=2)
    text_id = c.create_text(width/2, height/2, text=text, fill=fg,
                            font=("Segoe UI", 10, "bold"))

    # Hover effect (changes rectangle fill only)
    def on_enter(_): c.itemconfig(rect_id, fill=hover)
    def on_leave(_): c.itemconfig(rect_id, fill=bg)
    c.bind("<Enter>", on_enter)
    c.bind("<Leave>", on_leave)

    if command:
        c.bind("<Button-1>", lambda _: command())
    return c


# ---------- Main Application ----------
class AIPokemonGraderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Pokémon Grader App")
        self.geometry("1440x960")
        self.configure(bg="#212b31")

        self.container = tk.Frame(self, bg="#212b31")
        self.container.pack(fill="both", expand=True)

        self.pages = {}
        for PageClass in (MainPage, SettingsPage, HowItWorksPage):
            page = PageClass(parent=self.container, controller=self)
            self.pages[PageClass] = page
            page.place(relwidth=1, relheight=1)

        self.show_page(MainPage)

    def show_page(self, page_class):
        page = self.pages[page_class]
        page.tkraise()


# ---------- MAIN PAGE ----------
class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#212b31")  # Outer section color = title background
        self.controller = controller

        # --- Outer section frame spans top (title), middle (content), bottom (footer) ---
        outer_frame = tk.Frame(self, bg="#212b31")
        outer_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title = tk.Label(outer_frame, text="AI Pokémon Grader", font=("Segoe UI", 20, "bold"),
                         bg="#212b31", fg="#cad2c5")
        title.pack(pady=(10, 10))

        # --- Inner content frame (lighter blue-grey) ---
        content_frame = tk.Frame(outer_frame, bg="#353F47")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Instruction label
        label = tk.Label(content_frame, text="Select an image to upload:",
                         font=("Segoe UI", 12), bg="#353F47", fg="#d8e2dc")
        label.pack(pady=(10, 6))

        # File selection
        self.selected_file = tk.StringVar(value="No file selected")

        def browse_file():
            file_path = filedialog.askopenfilename(
                title="Select an Image",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                           ("All Files", "*.*")]
            )
            if file_path:
                self.selected_file.set(file_path)

        file_frame = tk.Frame(content_frame, bg="#353F47")
        file_frame.pack(pady=8)

        browse_btn = rect_button(file_frame, "Browse Files", command=browse_file,
                                 width=150, height=36)
        browse_btn.pack(side="left", padx=(0, 10))

        file_label = tk.Label(file_frame, textvariable=self.selected_file, bg="#353F47",
                              fg="#cad2c5", font=("Segoe UI", 10), anchor="w")
        file_label.pack(side="left", padx=5)

        # Submit button
        def on_submit():
            print("Selected file:", self.selected_file.get())

        submit_canvas = rect_button(content_frame, "Submit", command=on_submit,
                                    width=120, height=36)
        submit_canvas.pack(pady=10)

        # Bottom buttons frame
        bottom_frame = tk.Frame(content_frame, bg="#353F47")
        bottom_frame.pack(side="bottom", anchor="w", padx=30, pady=25)

        # Settings / Help button
        settings_btn = rect_button(bottom_frame, "Settings / Help",
                                   command=lambda: controller.show_page(SettingsPage),
                                   width=180, height=48)
        settings_btn.pack(side="left", padx=(0, 12))

        # How it Works button
        howitworks_btn = rect_button(bottom_frame, "How it works",
                                     command=lambda: controller.show_page(HowItWorksPage),
                                     width=180, height=48)
        howitworks_btn.pack(side="left")

        # Footer
        footer = tk.Label(outer_frame, text="© 2025 Logan Edwards", font=("Segoe UI", 9),
                          bg="#212b31", fg="#84a98c")
        footer.pack(side="bottom", pady=10)

# ---------- SETTINGS / HELP PAGE ----------
class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#353F47")
        self.controller = controller

        back_btn = rect_button(self, "← Back",
                               command=lambda: controller.show_page(MainPage),
                               width=90, height=35)
        back_btn.place(x=30, y=30)

        title = tk.Label(self, text="Settings / Help",
                         font=("Segoe UI", 18, "bold"),
                         bg="#353F47", fg="#cad2c5")
        title.pack(pady=(80, 20))

        info_text = (
            "Settings page"
        )
        info_label = tk.Label(self, text=info_text, justify="center",
                              font=("Segoe UI", 11), bg="#353F47", fg="#d8e2dc")
        info_label.pack(pady=20)


# ---------- HOW IT WORKS PAGE ----------
class HowItWorksPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#353F47")
        self.controller = controller

        back_btn = rect_button(self, "← Back",
                               command=lambda: controller.show_page(MainPage),
                               width=90, height=35)
        back_btn.place(x=30, y=30)

        title = tk.Label(self, text="How It Works",
                         font=("Segoe UI", 18, "bold"),
                         bg="#353F47", fg="#cad2c5")
        title.pack(pady=(80, 20))

        info_text = (
            "How it works page..."
        )
        info_label = tk.Label(self, text=info_text, justify="center",
                              font=("Segoe UI", 11), bg="#353F47", fg="#d8e2dc")
        info_label.pack(pady=20)


# ---------- RUN APP ----------
if __name__ == "__main__":
    app = AIPokemonGraderApp()
    app.mainloop()
