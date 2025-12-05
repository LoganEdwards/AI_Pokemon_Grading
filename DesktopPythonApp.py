import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
from MeasurementCalculator import process_single_card

import pickle
from Scikit_Learn_Model import predict_card_grade
from paths import resource_path

# ---------- Load Trained Model Pickle File ----------
model_path = resource_path("trained_model.pkl")
with open(model_path, "rb") as f:
    model = pickle.load(f)

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

        self.latest_prediction = None
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
            file_path = self.selected_file.get()
            if file_path == "No file selected":
                return

            print("Selected file:", file_path)

            # Step 1: Run measurement calculator
            measurement_data = process_single_card(file_path)
            if measurement_data is None:
                print("Error: MeasurementCalculator returned None")
                return

            surface = measurement_data.get("surface", 0)
            corners = measurement_data.get("corners", 0)
            centering_h = measurement_data.get("centering_h", 0)
            centering_v = measurement_data.get("centering_v", 0)

            # Step 2: Predict grade
            prediction = predict_card_grade(surface, corners, centering_h, centering_v)
            predicted_grade = prediction["predicted_grade"]

            # Step 3: Determine similarly graded card
            if predicted_grade >= 9.5:
                img_name = "10.0PSA_Charizard.png"
            elif predicted_grade >= 8.5:
                img_name = "9.0PSA_Charizard.png"
            elif predicted_grade >= 7.5:
                img_name = "8.0PSA_Charizard.png"
            elif predicted_grade >= 6.5:
                img_name = "7.0PSA_Charizard.png"
            elif predicted_grade >= 5.5:
                img_name = "6.0PSA_Charizard.png"
            elif predicted_grade >= 4.5:
                img_name = "5.0PSA_Charizard.png"
            elif predicted_grade >= 3.5:
                img_name = "4.0PSA_Charizard.png"
            elif predicted_grade >= 2.5:
                img_name = "3.0PSA_Charizard.png"
            elif predicted_grade >= 1.5:
                img_name = "2.0PSA_Charizard.png"
            else:
                img_name = "1.0PSA_Charizard.png"

            similar_card_path = resource_path(os.path.join("referenceImages", img_name))

            # Step 4: Package results for UI
            user_data = {
            "grade": predicted_grade,
            "surface": surface,
            "corners": corners,
            "centering_h": centering_h,
            "centering_v": centering_v,
            "similar_card_path": similar_card_path
            }


            # Step 5: Navigate to results page & update view
            controller.show_page(ResultsPage)
            results_page = controller.pages[ResultsPage]
            results_page.show_submitted_file(file_path)
            results_page.update_results(user_data)


        # function to enable/disable submit button depending on whether a file is selected
        # Submit button
        submit_canvas = rect_button(content_frame, "Submit", command=on_submit,
                                    width=120, height=36)
        submit_canvas.pack(pady=10)

        # Now define the function that updates submit state
        def update_submit_state():
            path = self.selected_file.get()
            if path and path != "No file selected":
                # enable
                submit_canvas.default_bg = "#2b363c"
                submit_canvas.hover_bg = "#3c4a50"
                submit_canvas.itemconfig(submit_canvas.rect_id, fill=submit_canvas.default_bg)
                if not submit_canvas.bind("<Button-1>"):
                    submit_canvas.bind("<Button-1>", lambda _: on_submit())
            else:
                # disable
                submit_canvas.default_bg = "#6b6b6b"
                submit_canvas.hover_bg = "#6b6b6b"
                submit_canvas.itemconfig(submit_canvas.rect_id, fill=submit_canvas.default_bg)
                submit_canvas.unbind("<Button-1>")

        # initialize submit state
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
                img_path = resource_path(os.path.join("referenceImages", "DarkBackgroundReferenceImage.jpg"))

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

        title_label = tk.Label(
            title_bar,
            text="How It Works",
            font=("Segoe UI", 20, "bold"),
            bg="#212b31",
            fg="#cad2c5"
        )
        title_label.pack(pady=5)

        # Back Button (same as other pages)
        back_btn = rect_button(
            title_bar,
            "← Back",
            command=lambda: controller.show_page(MainPage),
            width=100,
            height=36
        )
        back_btn.pack(side="left", padx=20, pady=5)

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
                "• The data gathered from the card image is passed into the Scikit-Learn AI model.\n\n"
                "• The model is trained on real-world data from 100 officially PSA graded cards and 900\n"
                "  additional synthetic training samples generated from that dataset.\n\n"
                "• The Scikit-Learn model uses a Linear Forest Regressor to predict the overall card grade\n"
                "  based on multiple features.\n\n"
                "• Four measured values are used as inputs: surface condition, corner condition,\n"
                "  horizontal centering, and vertical centering.\n\n"
                "• These measured values are passed into the model, which then generates an estimated\n"
                "  card grade based on the learned training data.\n\n"
                "• The predicted grade is then displayed on the results page for the user to review."
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

        title_label = tk.Label(
            title_bar,
            text="Results",
            font=("Segoe UI", 20, "bold"),
            bg="#212b31",
            fg="#cad2c5"
        )
        title_label.pack(pady=5)

        back_btn = rect_button(
            title_bar,
            "← Back",
            command=lambda: controller.show_page(MainPage),
            width=100, height=36
        )
        back_btn.pack(side="left", padx=20, pady=5)


        inner_frame = tk.Frame(outer_frame, bg="#353F47")
        inner_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Dynamic grade label
        self.grade_label = tk.Label(
            inner_frame,
            text="Estimated PSA Grade:",
            font=("Segoe UI", 16, "bold"),
            bg="#353F47",
            fg="#d8e2dc"
        )
        self.grade_label.pack(pady=(10, 20))

        # Two side-by-side boxes
        bottom_frame = tk.Frame(inner_frame, bg="#353F47")
        bottom_frame.pack(fill="both", expand=True, padx=40, pady=10)

        # ========= LEFT BOX (Submitted Image Preview) =========
        self.left_box = tk.Frame(
            bottom_frame,
            bg="#2b363c",
            highlightbackground="#4a595f",
            highlightthickness=2
        )
        self.left_box.place(relx=0.05, rely=0, relwidth=0.4, relheight=0.9)

        left_title = tk.Label(
            self.left_box,
            text="Submitted Image",
            bg="#2b363c",
            fg="#cad2c5",
            font=("Segoe UI", 14, "bold")
        )
        left_title.pack(anchor="n", pady=10)

        self.submitted_placeholder = tk.Label(
            self.left_box,
            text="(No image submitted)",
            bg="#2b363c",
            fg="#cad2c5",
            font=("Segoe UI", 12, "italic")
        )
        self.submitted_placeholder.pack(expand=True)

        self.submitted_image_label = None
        self.submitted_tk_img = None


        # ========= RIGHT BOX (Similar Card Example) =========
        self.right_box = tk.Frame(
            bottom_frame,
            bg="#2b363c",
            highlightbackground="#4a595f",
            highlightthickness=2
        )
        self.right_box.place(relx=0.52, rely=0, relwidth=0.45, relheight=0.9)

        right_title = tk.Label(
            self.right_box,
            text="Similarly Graded Card",
            font=("Segoe UI", 14, "bold"),
            bg="#2b363c",
            fg="#cad2c5"
        )
        right_title.pack(anchor="n", pady=(10, 8))

       # Filename display
        # self.similar_filename_var = tk.StringVar(value="(No similar card yet)")
        # self.similar_filename_label = tk.Label(
        #     self.right_box,
        #     textvariable=self.similar_filename_var,
        #     font=("Segoe UI", 12, "italic"),
        #     bg="#2b363c",
        #     fg="#cad2c5"
        # )
        # self.similar_filename_label.pack(anchor="n", pady=(0, 5))

        # Placeholder / image for similar card
        self.similar_card_img_label = tk.Label(
            self.right_box,
            text="(No image yet)",
            bg="#2b363c",
            fg="#cad2c5",
            font=("Segoe UI", 12, "italic")
        )
        self.similar_card_img_label.pack(expand=True)

        # Keep a reference to the PhotoImage
        self.similar_tk_img = None


        # ========= Feedback Box =========
        feedback_box = tk.Frame(
            inner_frame,
            bg="#2b363c",
            highlightbackground="#4a595f",
            highlightthickness=2
        )
        feedback_box.pack(fill="x", padx=80, pady=(20, 30), ipady=10)

        feedback_title = tk.Label(
            feedback_box,
            text="Card Grading Feedback",
            font=("Segoe UI", 14, "bold"),
            bg="#2b363c",
            fg="#cad2c5"
        )
        feedback_title.pack(anchor="nw", padx=15, pady=(10, 6))

        self.feedback_text = tk.Text(
            feedback_box,
            height=6,
            bg="#2b363c",
            fg="#f0f0f0",
            font=("Segoe UI", 12),
            wrap="word",
            bd=0
        )
        self.feedback_text.insert("1.0", "(Your feedback will appear here.)")
        self.feedback_text.config(state="disabled")
        self.feedback_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))



    # ================= IMAGE UPDATE ================= #
    def show_submitted_file(self, file_path):
        try:
            if self.submitted_image_label:
                self.submitted_image_label.destroy()

            img = Image.open(file_path)

            self.left_box.update_idletasks()
            box_w = self.left_box.winfo_width()
            box_h = self.left_box.winfo_height() - 50

            img.thumbnail((box_w, box_h))
            self.submitted_tk_img = ImageTk.PhotoImage(img)

            self.submitted_image_label = tk.Label(
                self.left_box,
                image=self.submitted_tk_img,
                bg="#2b363c"
            )
            self.submitted_image_label.pack(expand=True)

            if self.submitted_placeholder:
                self.submitted_placeholder.destroy()

        except Exception as e:
            print("Error displaying submitted image:", e)



    # ================= RESULTS UPDATE ================= #
    def update_results(self, user_data):

        grade = user_data.get("grade", "N/A")
        # Extract values from model data
        surface = user_data.get("surface")
        corners = user_data.get("corners")
        cent_h = user_data.get("centering_h")
        cent_v = user_data.get("centering_v")

        feedback_lines = []

        # Helper 
        # ===== Surface & Corners Feedback =====
        def score_feedback(label, score):
            if score is None:
                return f"{label}: No data"
            diff = 10 - score  # distance from PSA 10
            if diff > 5:
                return f"{label}: {score:.2f} - severely damaged or below PSA 10 requirements"
            elif diff > 3:
                return f"{label}: {score:.2f} - fairly damaged or below PSA 10 standards"
            elif diff > 1.5:
                return f"{label}: {score:.2f} - decent quality but not meeting PSA 10 standards"
            else:
                return f"{label}: {score:.2f} - great quality, meets PSA 9-10 standard"

        feedback_lines.append(score_feedback("Surface", surface))
        feedback_lines.append(score_feedback("Corners", corners))

        # ===== Centering Feedback =====
        def center_feedback(label, score):
            if score is None:
                return f"{label}: No data"
            if score >= 0.85:
                return f"{label}: {score:.2f} - severely uneven centering"
            elif score >= 0.70:
                return f"{label}: {score:.2f} - moderately uneven centering"
            elif score >= 0.65:
                return f"{label}: {score:.2f} - decent centering"
            else:
                return f"{label}: {score:.2f} - near-perfect centering valid for PSA 9-10"

        feedback_lines.append(center_feedback("Centering H", cent_h))
        feedback_lines.append(center_feedback("Centering V", cent_v))

        # Join feedback text
        feedback = "\n".join(feedback_lines)

        
        similar_path = user_data.get("similar_card_path", None)

        # Grade Text
        self.grade_label.config(text=f"Estimated PSA Grade: {grade}")

        # Feedback text
        self.feedback_text.config(state="normal")
        self.feedback_text.delete("1.0", "end")
        self.feedback_text.insert("1.0", feedback)
        self.feedback_text.config(state="disabled")

        # Similar card preview
        if similar_path:
            try:
                img = Image.open(similar_path)

                # Resize to fit the box while maintaining aspect ratio
                self.right_box.update_idletasks()
                box_w = self.right_box.winfo_width()
                box_h = self.right_box.winfo_height() - 40  # leave space for filename

                img.thumbnail((box_w, box_h), Image.LANCZOS)
                self.similar_tk_img = ImageTk.PhotoImage(img)  # keep reference!

                # Update label
                self.similar_card_img_label.config(image=self.similar_tk_img, text="")
                # self.similar_filename_var.set(similar_path.split("\\")[-1])  # only filename

            except Exception as e:
                print("Error loading similar card image:", e)
                self.similar_card_img_label.config(
                    text="(Failed to load similar card image)",
                    image=""
                )
                self.similar_filename_var.set("")
        else:
            # self.similar_card_img_label.config(text="(No similar card image available)", image="")
            self.similar_filename_var.set("")



# ---------- RUN APP ----------
if __name__ == "__main__":
    app = AIPokemonGraderApp()
    app.mainloop()
