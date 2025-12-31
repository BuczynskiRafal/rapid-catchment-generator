import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rcg.fuzzy.categories import LandCover, LandForm
from rcg.runner import generate_subcatchment
from rcg.validation import validate_area, validate_land_cover, validate_land_form


def get_help_file_path():
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "gui", "help_content.txt")


class Frame(tk.Frame):
    """Custom frame with styling"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg="#faf8f3")


class RcgApp:
    def __init__(self, root):
        self.root = root
        self.file_path = None
        self.setup_window()
        self.setup_styles()
        self.create_widgets()

    def setup_window(self):
        self.root.title("Rapid Catchment Generator")
        self.root.geometry("480x640")
        self.root.configure(bg="#faf8f3")
        self.root.resizable(False, False)

        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"480x640+{x}+{y}")

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Force theme to respect our colors
        self.root.option_add('*TButton*background', '#d97706')
        self.root.option_add('*TButton*foreground', 'white')

        # Configure Claude.ai inspired styles
        self.style.configure('Title.TLabel',
                           font=('Segoe UI', 20, 'bold'),
                           background="#faf8f3",
                           foreground="#2f1b14")

        self.style.configure('Subtitle.TLabel',
                           font=('Segoe UI', 10),
                           background="#faf8f3",
                           foreground="#8b7355")

        self.style.configure('CustomStyle.TLabel',
                           font=('Segoe UI', 11),
                           background="#faf8f3",
                           foreground="#5d4e37",
                           padding=(0, 5))

        self.style.configure('CustomStyle.TCombobox',
                           fieldbackground="white",
                           borderwidth=1,
                           relief="solid",
                           padding=(8, 8))

        self.style.configure('CustomStyle.TEntry',
                           fieldbackground="white",
                           borderwidth=1,
                           relief="solid",
                           padding=(8, 8))

        self.style.configure('Primary.TButton',
                           font=('Segoe UI', 11, 'bold'),
                           padding=(20, 12),
                           background="#d97706",
                           foreground="#ffffff",
                           borderwidth=0,
                           relief="flat",
                           focuscolor="none")

        self.style.configure('Success.TButton',
                           font=('Segoe UI', 11, 'bold'),
                           padding=(20, 12),
                           background="#2f9e44",
                           foreground="white",
                           borderwidth=0,
                           relief="flat",
                           focuscolor="none")

        self.style.configure('Info.TButton',
                           font=('Segoe UI', 10),
                           padding=(15, 12),
                           background="#a78b5c",
                           foreground="white",
                           borderwidth=0,
                           relief="flat",
                           focuscolor="none")

        # Map colors for hover effects - Claude.ai inspired
        self.style.map('Primary.TButton',
                      background=[('active', '#228be6'), ('!active', '#228be6')],
                      foreground=[('active', '#ffffff'), ('!active', '#ffffff')])
        self.style.map('Success.TButton',
                      background=[('active', '#2f9e44'), ('!active', '#2f9e44')],
                      foreground=[('active', 'white'), ('!active', 'white')])
        self.style.map('Info.TButton',
                      background=[('active', '#fab005'), ('!active', '#fab005')],
                      foreground=[('active', 'white'), ('!active', 'white')])

        # Fix combobox - remove all text selection highlighting
        self.style.map('CustomStyle.TCombobox',
                      selectbackground=[('readonly', 'white'), ('!readonly', 'white')],
                      selectforeground=[('readonly', '#5d4e37'), ('!readonly', '#5d4e37')],
                      fieldbackground=[('readonly', 'white'), ('!readonly', 'white')],
                      highlightcolor=[('readonly', 'white'), ('!readonly', 'white')])

    def create_widgets(self):
        main_frame = Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Header section
        header_frame = Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 30))

        title_label = ttk.Label(header_frame, text="Rapid Catchment Generator", style="Title.TLabel")
        title_label.pack()

        subtitle_label = ttk.Label(header_frame, text="Generate SWMM subcatchments with fuzzy logic", style="Subtitle.TLabel")
        subtitle_label.pack(pady=(5, 0))

        # Input section
        input_frame = Frame(main_frame)
        input_frame.pack(fill="x", pady=(0, 20))

        # Land cover selection - dynamically populated from categories
        self.create_input_group(input_frame, "Land Cover Type", 0)
        self.land_cover_var = tk.StringVar()
        land_cover_values = sorted(LandCover.get_all_categories())
        land_cover_combobox = ttk.Combobox(
            input_frame,
            textvariable=self.land_cover_var,
            values=land_cover_values,
            style="CustomStyle.TCombobox",
            state="readonly"
        )
        land_cover_combobox.pack(fill="x", pady=(5, 20))

        # Land form selection - dynamically populated from categories
        self.create_input_group(input_frame, "Land Form Type", 1)
        self.land_form_var = tk.StringVar()
        land_form_values = sorted(LandForm.get_all_categories())
        land_form_combobox = ttk.Combobox(
            input_frame,
            textvariable=self.land_form_var,
            values=land_form_values,
            style="CustomStyle.TCombobox",
            state="readonly"
        )
        land_form_combobox.pack(fill="x", pady=(5, 20))

        # Area input
        self.create_input_group(input_frame, "Area (hectares)", 2)
        self.area_var = tk.StringVar()
        area_entry = ttk.Entry(input_frame, textvariable=self.area_var, style="CustomStyle.TEntry")
        area_entry.pack(fill="x", pady=(5, 20))

        # File selection section
        file_frame = Frame(main_frame)
        file_frame.pack(fill="x", pady=(0, 20))

        self.create_input_group(file_frame, "SWMM Input File (.inp)", 3)

        file_select_frame = Frame(file_frame)
        file_select_frame.pack(fill="x", pady=(5, 10))

        self.selected_file_var = tk.StringVar()
        self.selected_file_entry = ttk.Entry(
            file_select_frame,
            textvariable=self.selected_file_var,
            style="CustomStyle.TEntry",
            state="readonly"
        )
        self.selected_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        choose_file_button = ttk.Button(
            file_select_frame,
            text="Browse",
            command=self.choose_file,
            style="Primary.TButton"
        )
        choose_file_button.pack(side="right")

        # Action buttons section
        button_frame = Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))

        run_button = ttk.Button(
            button_frame,
            text="Run Simulation",
            command=self.run_simulation,
            style="Success.TButton",
        )
        run_button.pack(fill="x", pady=(0, 10))

        help_button = ttk.Button(
            button_frame,
            text="Help & Documentation",
            command=self.show_help,
            style="Primary.TButton"
        )
        help_button.pack(fill="x",)

    def create_input_group(self, parent, text, row):
        label = ttk.Label(parent, text=text, style="CustomStyle.TLabel")
        label.pack(anchor="w")

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Help - Categories and Instructions")
        help_window.geometry("500x600")
        help_window.configure(bg="#faf8f3")
        help_window.resizable(True, True)

        # Center help window
        help_window.update_idletasks()
        x = (help_window.winfo_screenwidth() - help_window.winfo_width()) // 2
        y = (help_window.winfo_screenheight() - help_window.winfo_height()) // 2
        help_window.geometry(f"500x600+{x}+{y}")

        help_frame = Frame(help_window)
        help_frame.pack(fill="both", expand=True, padx=20, pady=20)

        help_title = ttk.Label(help_frame, text="Help & Documentation", style="Title.TLabel")
        help_title.pack(pady=(0, 20))

        try:
            with open(get_help_file_path()) as file:
                text = file.read()
        except FileNotFoundError:
            text = """
RAPID CATCHMENT GENERATOR HELP

This application generates SWMM subcatchments using fuzzy logic based on:

LAND COVER TYPES:
• permeable_areas - Natural permeable surfaces
• permeable_terrain_on_plains - Open permeable terrain
• mountains_vegetated - Vegetated mountain areas
• mountains_rocky - Rocky mountain surfaces
• urban_weakly_impervious - Low density urban areas
• urban_moderately_impervious - Medium density urban areas
• urban_highly_impervious - High density urban areas
• suburban_weakly_impervious - Low density suburban areas
• suburban_highly_impervious - High density suburban areas
• rural - Rural areas
• forests - Forested areas
• meadows - Grassland and meadows
• arable - Agricultural land
• marshes - Wetlands and marshes

LAND FORM TYPES:
• marshes_and_lowlands - Flat, low-lying areas
• flats_and_plateaus - Flat elevated areas
• flats_and_plateaus_in_combination_with_hills - Mixed flat and hilly terrain
• hills_with_gentle_slopes - Gently sloping hills
• steeper_hills_and_foothills - Steeper hill terrain
• hills_and_outcrops_of_mountain_ranges - Mountain foothills
• higher_hills - High elevation hills
• mountains - Mountain terrain
• highest_mountains - High mountain peaks

USAGE:
1. Select appropriate land cover and land form types
2. Enter area in hectares (positive number)
3. Select your SWMM .inp file
4. Click "Run Simulation"

The application will generate subcatchments with appropriate parameters based on fuzzy logic rules.
            """

        # Create scrollable text widget
        text_frame = tk.Frame(help_frame, bg="#faf8f3")
        text_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        help_text = tk.Text(
            text_frame,
            wrap="word",
            yscrollcommand=scrollbar.set,
            font=('Segoe UI', 10),
            bg="#ffffff",
            fg="#5d4e37",
            relief="flat",
            borderwidth=1,
            padx=15,
            pady=15
        )
        help_text.insert(tk.END, text)
        help_text.config(state="disabled")
        help_text.pack(side="left", fill="both", expand=True)

        scrollbar.config(command=help_text.yview)

    def choose_file(self):
        file_path = filedialog.askopenfilename(
            title="Select SWMM Input File",
            filetypes=(("SWMM files", "*.inp"), ("All files", "*.*")),
        )
        if file_path:
            file_extension = os.path.splitext(file_path)[1]
            if file_extension.lower() != ".inp":
                messagebox.showerror(
                    "Invalid File Type",
                    "Please select a file with the '.inp' extension."
                )
                return

            self.selected_file_var.set(os.path.basename(file_path))
            self.file_path = file_path

    def run_simulation(self):
        """Run the subcatchment generation with centralized validation."""
        land_cover_str = self.land_cover_var.get()
        land_form_str = self.land_form_var.get()
        area_str = self.area_var.get()

        # Basic presence validation
        if not self.file_path:
            messagebox.showerror("Missing File", "Please select a SWMM input file.")
            return

        if not land_cover_str:
            messagebox.showerror("Missing Selection", "Please select a land cover type.")
            return

        if not land_form_str:
            messagebox.showerror("Missing Selection", "Please select a land form type.")
            return

        if not area_str:
            messagebox.showerror("Missing Value", "Please enter an area value.")
            return

        # Use centralized validation
        try:
            # Handle comma as decimal separator
            area_str = area_str.replace(",", ".")
            area = validate_area(area_str)
        except Exception as e:
            messagebox.showerror("Invalid Area", str(e))
            return

        try:
            validate_land_form(land_form_str)
        except Exception as e:
            messagebox.showerror("Invalid Land Form", str(e))
            return

        try:
            validate_land_cover(land_cover_str)
        except Exception as e:
            messagebox.showerror("Invalid Land Cover", str(e))
            return

        # Generate subcatchment
        try:
            generate_subcatchment(self.file_path, area, land_form_str, land_cover_str)
            messagebox.showinfo(
                "Simulation Complete",
                f"Subcatchment generated successfully!\n\n"
                f"Area: {area} ha\n"
                f"Land Cover: {land_cover_str.replace('_', ' ').title()}\n"
                f"Land Form: {land_form_str.replace('_', ' ').title()}\n"
                f"File: {os.path.basename(self.file_path)}"
            )
        except Exception as e:
            messagebox.showerror("Simulation Error", f"An error occurred during simulation:\n\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = RcgApp(root)
    root.mainloop()
