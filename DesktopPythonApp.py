import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

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

    # store attributes on canvas so callers can modify appearance / behavior
    c.rect_id = rect_id
    c.text_id = text_id
    c.default_bg = bg
    c.hover_bg = hover
    c.fg = fg
    c.outline = outline
    c._command = command

    # Hover effect (reads current attributes so they can be changed externally)
    def on_enter(_):
        try:
            c.itemconfig(c.rect_id, fill=c.hover_bg)
        except Exception:
            pass

    def on_leave(_):
        try:
            c.itemconfig(c.rect_id, fill=c.default_bg)
        except Exception:
            pass

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
        # add ResultsPage to the list so it is available for navigation
        for PageClass in (MainPage, SettingsPage, HowItWorksPage, ResultsPage):
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
            else:
                # if user cancels, keep "No file selected"
                self.selected_file.set("No file selected")
            update_submit_state()

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
            # for now we simply print and navigate to results page
            print("Selected file:", self.selected_file.get())
            # You can later pass the path/data to the ResultsPage via attributes or a method.
            controller.show_page(ResultsPage)
            # populate results page placeholders if desired:
            results_page = controller.pages[ResultsPage]
            results_page.show_submitted_file(self.selected_file.get())

        submit_canvas = rect_button(content_frame, "Submit", command=on_submit,
                                    width=120, height=36)
        submit_canvas.pack(pady=10)

        # function to enable/disable submit button depending on whether a file is selected
        def update_submit_state():
            path = self.selected_file.get()
            if path and path != "No file selected":
                # enable
                submit_canvas.default_bg = "#2b363c"
                submit_canvas.hover_bg = "#3c4a50"
                submit_canvas.itemconfig(submit_canvas.rect_id, fill=submit_canvas.default_bg)
                # ensure click bound
                if not submit_canvas.bind("<Button-1>"):
                    submit_canvas.bind("<Button-1>", lambda _: on_submit())
                # ensure hover handlers available (they already are; attributes updated above)
            else:
                # disable: greyed out, no click
                submit_canvas.default_bg = "#6b6b6b"
                submit_canvas.hover_bg = "#6b6b6b"
                submit_canvas.itemconfig(submit_canvas.rect_id, fill=submit_canvas.default_bg)
                # remove click binding
                submit_canvas.unbind("<Button-1>")

        # initialize submit state (disabled by default)
        update_submit_state()

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
        super().__init__(parent, bg="#212b31")  # same as main page background
        self.controller = controller

        # ==== Outer border ====
        outer_frame = tk.Frame(self, bg="#212b31")
        outer_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ==== Title bar ====
        title_bar = tk.Frame(outer_frame, bg="#212b31")
        title_bar.pack(fill="x", pady=(5, 10))

        title_label = tk.Label(
            title_bar,
            text="Settings and Help",
            font=("Segoe UI", 20, "bold"),
            bg="#212b31",
            fg="#cad2c5"
        )
        title_label.pack(pady=5)

        # Back button styled like others
        back_btn = rect_button(
            title_bar,
            "← Back",
            command=lambda: controller.show_page(MainPage),
            width=100, height=36
        )
        back_btn.pack(side="left", padx=20, pady=5)

        # ==== Inner content (lighter section) ====
        inner_frame = tk.Frame(outer_frame, bg="#353F47")
        inner_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # ==== Section 1: How to Upload Header ====
        upload_label = tk.Label(
            inner_frame,
            text="How to Upload an Image",
            font=("Segoe UI", 14, "bold"),
            bg="#353F47",
            fg="#d8e2dc"
        )
        upload_label.pack(pady=(15, 8))

        # ==== Middle Box for Steps to upload image ====
        steps_box = tk.Frame(inner_frame, bg="#2b363c", highlightbackground="#4a595f", highlightthickness=2)
        steps_box.pack(pady=(5, 20), ipadx=10, ipady=10, fill="x", padx=80)

        steps_text = tk.Label(
            steps_box,
            text=(
                "1. First select the box on the main page labeled (Browse Files).\n"
                "2. Next search for the card you wish to upload.\n"
                "3. Ensure that this file is a .jpg, .jpeg, .bmp, or .png file before uploading.\n"
                "4. After selecting the file, check that the path is correct and hit the submit button below."
            ),
            font=("Segoe UI", 15),
            bg="#2b363c",
            fg="#f0f0f0",  # brighter text for readability
            justify="left",
            wraplength=900
        )
        steps_text.pack(anchor="w", padx=15, pady=10)

        # ==== Bottom two sections ====
        bottom_frame = tk.Frame(inner_frame, bg="#353F47")
        bottom_frame.pack(fill="both", expand=True, padx=40, pady=(10, 20))

        # Left: image placeholder (replaced with actual reference image using PIL)
        # Left: image placeholder (replaced with actual reference image using PIL)
        left_box = tk.Frame(
            bottom_frame,
            bg="#2b363c",
            highlightbackground="#4a595f",
            highlightthickness=2
        )
        left_box.place(relx=0.05, rely=0, relwidth=0.35, relheight=0.9)

        # Title at the top of the box
        left_title = tk.Label(
            left_box,
            text="Reference Image",
            bg="#2b363c",
            fg="#cad2c5",
            font=("Segoe UI", 14, "bold")
        )
        left_title.pack(anchor="n", pady=(10, 10))


        # --- Function that runs AFTER the box is rendered ---
        def load_ref_image():

            try:
                img_path = r"C:\Users\LEdwa\AI_Pokegrader\referenceImages\DarkBackgroundReferenceImage.jpg"

                pil_img = Image.open(img_path)

                # Now the box has *real* size values
                left_box.update_idletasks()
                box_w = left_box.winfo_width()
                box_h = left_box.winfo_height() - 60  # leave room for title

                # Maintain aspect ratio
                img_w, img_h = pil_img.size
                scale = min(box_w / img_w, box_h / img_h)

                new_w = int(img_w * scale)
                new_h = int(img_h * scale)

                pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)

                # Convert to Tk image
                self.ref_img = ImageTk.PhotoImage(pil_img)

                # Display image
                left_img_label = tk.Label(left_box, image=self.ref_img, bg="#2b363c")
                left_img_label.pack(expand=True)

            except Exception as e:
                fallback = tk.Label(
                    left_box,
                    text="(Reference image failed to load)",
                    bg="#2b363c",
                    fg="#cad2c5",
                    font=("Segoe UI", 12, "italic")
                )
                fallback.pack(expand=True)
                print("Image load error:", e)

        # Delay image loading → fixes width=0 / height=0 error
        left_box.after(100, load_ref_image)

        # Right: Things to Avoid (unchanged)
        right_box = tk.Frame(bottom_frame, bg="#2b363c", highlightbackground="#4a595f", highlightthickness=2)
        right_box.place(relx=0.45, rely=0, relwidth=0.5, relheight=0.8)  # already 0.8

        right_label = tk.Label(
            right_box,
            text="Things to Look Out For:",
            bg="#2b363c",
            fg="#f0f0f0",
            font=("Segoe UI", 16, "bold"),
            anchor="w"
        )
        right_label.pack(anchor="w", padx=15, pady=(10, 0))

        bullets = "\n\n".join([
            "• Avoid steep camera angles, try to get a direct 90 degree shot from above.",
            "• Avoid shadows or dimly lit rooms. Use even lighting to avoid glare.",
            "• Do not block the front of the card, remove any sleeves or holders.",
            "• Use a clear dark background and avoid anything else visible other than the card.",
            "• Ensure the entire card is visible in the frame, fill the majority of the frame with the card."
        ])

        bullet_label = tk.Label(
            right_box,
            text=bullets,
            bg="#2b363c",
            fg="#f0f0f0",
            font=("Segoe UI", 14),
            justify="left",
            wraplength=400
        )
        bullet_label.pack(anchor="w", padx=20, pady=10)


# ---------- HOW IT WORKS PAGE ----------
class HowItWorksPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#212b31")  # match main background
        self.controller = controller

        # ==== Outer Frame ====
        outer_frame = tk.Frame(self, bg="#212b31")
        outer_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ==== Title Bar ====
        title_bar = tk.Frame(outer_frame, bg="#212b31")
        title_bar.pack(fill="x", pady=(5, 15))

        # Back Button (same as other pages)
        back_btn = rect_button(
            title_bar,
            "← Back",
            command=lambda: controller.show_page(MainPage),
            width=100,
            height=36
        )
        back_btn.pack(side="left", padx=20, pady=5)

        title_label = tk.Label(
            title_bar,
            text="How It Works",
            font=("Segoe UI", 20, "bold"),
            bg="#212b31",
            fg="#cad2c5"
        )
        title_label.pack(pady=5)

        # ==== Inner Area ====
        inner_frame = tk.Frame(outer_frame, bg="#353F47")
        inner_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # ==== Two Side-By-Side Sections ====
        bottom_frame = tk.Frame(inner_frame, bg="#353F47")
        bottom_frame.pack(fill="both", expand=True, padx=40, pady=30)

        # ------------------------------------------------------
        # LEFT BOX — "How the data is gathered from the image"
        # ------------------------------------------------------
        left_box = tk.Frame(
            bottom_frame,
            bg="#2b363c",
            highlightbackground="#4a595f",
            highlightthickness=2
        )
        left_box.place(relx=0.03, rely=0, relwidth=0.44, relheight=0.85)

        left_title = tk.Label(
            left_box,
            text="How the Data is Gathered From the Image",
            font=("Segoe UI", 15, "bold"),
            bg="#2b363c",
            fg="#cad2c5",
            wraplength=380
        )
        left_title.pack(anchor="n", pady=(15, 10))

        left_text = tk.Label(
            left_box,
            text=(
                "• The card image is loaded and checked for validity.\n\n"
                "• The program detects the card contour by scanning inward from the edges "
                "to find the solid border.\n\n"
                "• A perspective transform is applied to straighten the card.\n\n"
                "• The pixel-to-millimeter ratio is calculated to map image dimensions to "
                "real-world card size.\n\n"
                "• Inner artwork is detected, with a fallback to a default bounding box if "
                "detection fails.\n\n"
                "• Measurements include left, right, top, and bottom margins, surface features, "
                "corner conditions, and centering ratios.\n\n"
                "• These values are compiled into a structured data profile for scoring."
            ),
            font=("Segoe UI", 13),
            bg="#2b363c",
            fg="#f0f0f0",
            justify="left",
            wraplength=380
        )
        left_text.pack(anchor="nw", padx=20, pady=10)

        # ------------------------------------------------------
        # RIGHT BOX — "How the AI model works"
        # ------------------------------------------------------
        right_box = tk.Frame(
            bottom_frame,
            bg="#2b363c",
            highlightbackground="#4a595f",
            highlightthickness=2
        )
        right_box.place(relx=0.52, rely=0, relwidth=0.45, relheight=0.85)

        right_title = tk.Label(
            right_box,
            text="How the AI Model Works",
            font=("Segoe UI", 15, "bold"),
            bg="#2b363c",
            fg="#cad2c5",
            wraplength=380
        )
        right_title.pack(anchor="n", pady=(15, 10))

        right_text = tk.Label(
            right_box,
            text=(
                "• The data gathered from the image is passed into the Scikit learn AI model.\n\n"
                "• The Scikit model is trained on data gathered from ~500 images of PSA graded cards.\n\n"
                "• The model uses a __________ (Fill in later) algorithm to make an estimatation based on the user data\n\n"
                "• The output is then displayed on the results page for review."
            ),
            font=("Segoe UI", 13),
            bg="#2b363c",
            fg="#f0f0f0",
            justify="left",
            wraplength=380
        )
        right_text.pack(anchor="nw", padx=20, pady=10)


# ---------- RESULTS PAGE ----------
class ResultsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#212b31")
        self.controller = controller

        outer_frame = tk.Frame(self, bg="#212b31")
        outer_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title bar + back button
        title_bar = tk.Frame(outer_frame, bg="#212b31")
        title_bar.pack(fill="x", pady=(5, 15))

        back_btn = rect_button(
            title_bar,
            "← Back",
            command=lambda: controller.show_page(MainPage),
            width=100, height=36
        )
        back_btn.pack(side="left", padx=20, pady=5)

        title_label = tk.Label(
            title_bar,
            text="Results",
            font=("Segoe UI", 20, "bold"),
            bg="#212b31",
            fg="#cad2c5"
        )
        title_label.pack(pady=5)

        inner_frame = tk.Frame(outer_frame, bg="#353F47")
        inner_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Subheading for estimated grade
        subheading = tk.Label(
            inner_frame,
            text="Estimated PSA Grade: ______",
            font=("Segoe UI", 16, "bold"),
            bg="#353F47",
            fg="#d8e2dc"
        )
        subheading.pack(pady=(10, 20))

        # Two side-by-side boxes
        bottom_frame = tk.Frame(inner_frame, bg="#353F47")
        bottom_frame.pack(fill="both", expand=True, padx=40, pady=10)

        left_box = tk.Frame(bottom_frame, bg="#2b363c", highlightbackground="#4a595f", highlightthickness=2)
        left_box.place(relx=0.03, rely=0, relwidth=0.44, relheight=0.6)

        left_title = tk.Label(
            left_box,
            text="Submitted Card",
            font=("Segoe UI", 14, "bold"),
            bg="#2b363c",
            fg="#cad2c5"
        )
        left_title.pack(anchor="n", pady=(10, 8))

        # placeholder for the submitted image / details
        self.submitted_placeholder = tk.Label(
            left_box,
            text="(Submitted card preview will appear here)",
            bg="#2b363c",
            fg="#f0f0f0",
            font=("Segoe UI", 12),
            wraplength=320,
            justify="center"
        )
        self.submitted_placeholder.pack(expand=True, pady=20)

        right_box = tk.Frame(bottom_frame, bg="#2b363c", highlightbackground="#4a595f", highlightthickness=2)
        right_box.place(relx=0.52, rely=0, relwidth=0.45, relheight=0.6)

        right_title = tk.Label(
            right_box,
            text="Similarly Graded Card",
            font=("Segoe UI", 14, "bold"),
            bg="#2b363c",
            fg="#cad2c5"
        )
        right_title.pack(anchor="n", pady=(10, 8))

        self.similar_placeholder = tk.Label(
            right_box,
            text="(A similarly graded card example will appear here)",
            bg="#2b363c",
            fg="#f0f0f0",
            font=("Segoe UI", 12),
            wraplength=320,
            justify="center"
        )
        self.similar_placeholder.pack(expand=True, pady=20)

        # Bottom paragraph-sized box with heading "Card Grading Feedback"
        feedback_box = tk.Frame(inner_frame, bg="#2b363c", highlightbackground="#4a595f", highlightthickness=2)
        feedback_box.pack(fill="x", padx=80, pady=(20, 30), ipady=10)

        feedback_title = tk.Label(
            feedback_box,
            text="Card Grading Feedback",
            font=("Segoe UI", 14, "bold"),
            bg="#2b363c",
            fg="#cad2c5"
        )
        feedback_title.pack(anchor="nw", padx=15, pady=(10, 6))

        # Use a Text widget so the feedback can be long; initially read-only / placeholder text
        self.feedback_text = tk.Text(feedback_box, height=6, bg="#2b363c", fg="#f0f0f0",
                                     font=("Segoe UI", 12), wrap="word", bd=0)
        self.feedback_text.insert("1.0", "Feedback about the card grading will appear here. This can include surface notes, corner condition notes, centering, and other details.")
        self.feedback_text.config(state="disabled")
        self.feedback_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))

    def show_submitted_file(self, filepath):
        """Placeholder method — called when submit is pressed.
        Currently writes the filepath into the Submitted Card placeholder.
        Later: load & display thumbnail, or populate feedback and similar card."""
        if filepath and filepath != "No file selected":
            self.submitted_placeholder.config(text=f"Submitted file:\n{filepath}")
        else:
            self.submitted_placeholder.config(text="(No file provided)")


# ---------- RUN APP ----------
if __name__ == "__main__":
    app = AIPokemonGraderApp()
    app.mainloop()
