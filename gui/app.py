import os
import sys
from tkinter import filedialog, messagebox

import customtkinter as ctk

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


class RcgApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.file_path = None
        self.setup_window()
        self.create_widgets()

    def setup_window(self):
        self.title("Rapid Catchment Generator")
        self.geometry("540x840")
        self.resizable(False, False)

        # Set appearance mode and color theme
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 540) // 2
        y = (self.winfo_screenheight() - 760) // 2
        self.geometry(f"540x840+{x}+{y}")

    def create_widgets(self):
        # Main container with padding
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # Header section
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 30))

        title_label = ctk.CTkLabel(
            header_frame,
            text="Rapid Catchment Generator",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=("#1a1a2e", "#e0e0e0"),
        )
        title_label.pack()

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Generate SWMM subcatchments with fuzzy logic",
            font=ctk.CTkFont(size=13),
            text_color=("#6b7280", "#9ca3af"),
        )
        subtitle_label.pack(pady=(8, 0))

        # Input card
        input_card = ctk.CTkFrame(main_frame, corner_radius=16)
        input_card.pack(fill="x", pady=(0, 20))

        input_inner = ctk.CTkFrame(input_card, fg_color="transparent")
        input_inner.pack(fill="x", padx=24, pady=24)

        # Land cover selection
        land_cover_label = ctk.CTkLabel(
            input_inner,
            text="Land Cover Type",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        land_cover_label.pack(fill="x", pady=(0, 8))

        land_cover_values = sorted(LandCover.get_all_categories())
        self.land_cover_var = ctk.StringVar(value="")
        self.land_cover_dropdown = ctk.CTkComboBox(
            input_inner,
            variable=self.land_cover_var,
            values=land_cover_values,
            height=42,
            corner_radius=10,
            border_width=1,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12),
            state="readonly",
        )
        self.land_cover_dropdown.pack(fill="x", pady=(0, 20))
        self.land_cover_dropdown.set("")

        # Land form selection
        land_form_label = ctk.CTkLabel(
            input_inner,
            text="Land Form Type",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        land_form_label.pack(fill="x", pady=(0, 8))

        land_form_values = sorted(LandForm.get_all_categories())
        self.land_form_var = ctk.StringVar(value="")
        self.land_form_dropdown = ctk.CTkComboBox(
            input_inner,
            variable=self.land_form_var,
            values=land_form_values,
            height=42,
            corner_radius=10,
            border_width=1,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12),
            state="readonly",
        )
        self.land_form_dropdown.pack(fill="x", pady=(0, 20))
        self.land_form_dropdown.set("")

        # Area input
        area_label = ctk.CTkLabel(
            input_inner,
            text="Area (hectares)",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        area_label.pack(fill="x", pady=(0, 8))

        self.area_entry = ctk.CTkEntry(
            input_inner,
            height=42,
            corner_radius=10,
            border_width=1,
            font=ctk.CTkFont(size=13),
            placeholder_text="Enter area value...",
        )
        self.area_entry.pack(fill="x")

        # File selection card
        file_card = ctk.CTkFrame(main_frame, corner_radius=16)
        file_card.pack(fill="x", pady=(0, 24))

        file_inner = ctk.CTkFrame(file_card, fg_color="transparent")
        file_inner.pack(fill="x", padx=24, pady=24)

        file_label = ctk.CTkLabel(
            file_inner,
            text="SWMM Input File (.inp)",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        file_label.pack(fill="x", pady=(0, 8))

        file_select_frame = ctk.CTkFrame(file_inner, fg_color="transparent")
        file_select_frame.pack(fill="x")

        self.selected_file_var = ctk.StringVar(value="")
        self.selected_file_entry = ctk.CTkEntry(
            file_select_frame,
            textvariable=self.selected_file_var,
            height=42,
            corner_radius=10,
            border_width=1,
            font=ctk.CTkFont(size=13),
            state="disabled",
            placeholder_text="No file selected",
        )
        self.selected_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))

        choose_file_button = ctk.CTkButton(
            file_select_frame,
            text="Browse",
            command=self.choose_file,
            width=100,
            height=42,
            corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#3b82f6", "#2563eb"),
            hover_color=("#2563eb", "#1d4ed8"),
        )
        choose_file_button.pack(side="right")

        # Action buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 0))

        run_button = ctk.CTkButton(
            button_frame,
            text="Run Simulation",
            command=self.run_simulation,
            height=48,
            corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#22c55e", "#16a34a"),
            hover_color=("#16a34a", "#15803d"),
        )
        run_button.pack(fill="x", pady=(0, 12))

        help_button = ctk.CTkButton(
            button_frame,
            text="Help & Documentation",
            command=self.show_help,
            height=48,
            corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=("#6366f1", "#4f46e5"),
            hover_color=("#4f46e5", "#4338ca"),
        )
        help_button.pack(fill="x", pady=(0, 12))

        # Theme toggle
        theme_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        theme_frame.pack(fill="x")

        self.theme_switch = ctk.CTkSwitch(
            theme_frame,
            text="Dark Mode",
            command=self.toggle_theme,
            font=ctk.CTkFont(size=12),
            progress_color=("#3b82f6", "#2563eb"),
        )
        self.theme_switch.pack(anchor="center")

    def toggle_theme(self):
        if self.theme_switch.get():
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def show_help(self):
        help_window = ctk.CTkToplevel(self)
        help_window.title("Help - Categories and Instructions")
        help_window.geometry("560x650")
        help_window.resizable(True, True)

        # Center help window
        help_window.update_idletasks()
        x = (help_window.winfo_screenwidth() - 560) // 2
        y = (help_window.winfo_screenheight() - 650) // 2
        help_window.geometry(f"560x650+{x}+{y}")

        # Make it modal
        help_window.transient(self)
        help_window.grab_set()

        help_frame = ctk.CTkFrame(help_window, fg_color="transparent")
        help_frame.pack(fill="both", expand=True, padx=24, pady=24)

        help_title = ctk.CTkLabel(
            help_frame,
            text="Help & Documentation",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
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

        # Scrollable text widget
        help_textbox = ctk.CTkTextbox(
            help_frame,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            wrap="word",
        )
        help_textbox.pack(fill="both", expand=True)
        help_textbox.insert("1.0", text.strip())
        help_textbox.configure(state="disabled")

        # Close button
        close_button = ctk.CTkButton(
            help_frame,
            text="Close",
            command=help_window.destroy,
            height=42,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        close_button.pack(pady=(16, 0))

    def choose_file(self):
        file_path = filedialog.askopenfilename(
            title="Select SWMM Input File",
            filetypes=(("SWMM files", "*.inp"), ("All files", "*.*")),
        )
        if file_path:
            file_extension = os.path.splitext(file_path)[1]
            if file_extension.lower() != ".inp":
                messagebox.showerror("Invalid File Type", "Please select a file with the '.inp' extension.")
                return

            self.selected_file_var.set(os.path.basename(file_path))
            self.file_path = file_path

    def run_simulation(self):
        """Run the subcatchment generation with centralized validation."""
        land_cover_str = self.land_cover_var.get()
        land_form_str = self.land_form_var.get()
        area_str = self.area_entry.get()

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
                f"File: {os.path.basename(self.file_path)}",
            )
        except Exception as e:
            messagebox.showerror("Simulation Error", f"An error occurred during simulation:\n\n{str(e)}")


def main():
    app = RcgApp()
    app.mainloop()


if __name__ == "__main__":
    main()
