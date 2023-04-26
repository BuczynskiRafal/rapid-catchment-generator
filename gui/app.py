import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rcg.runner import generate_subcatchment


class RcgApp:
    def __init__(self, root):
        self.root = root
        self.file_path = None
        self.root.title("Rapid Catchment Generator")
        self.set_window_size(width=340, height=270)
        self.create_widgets()

    def set_window_size(self, width, height):
        self.root.geometry(f"{width}x{height}")

    def create_widgets(self):
        # Tworzenie rozwijanej listy LandCover
        land_cover_label = tk.Label(self.root, text="Select land cover type:")
        land_cover_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.land_cover_var = tk.StringVar()
        land_cover_combobox = ttk.Combobox(
            self.root,
            textvariable=self.land_cover_var, 
            values=[
                "medium conditions",
                "permeable areas",
                "permeable terrain on plains",
                "hilly",
                "mountains",
                "bare rocky slopes",
                "urban",
                "suburban",
                "rural",
                "forests",
                "meadows",
                "arable",
                "marshes",
            ],
            width=25
            )
        land_cover_combobox.grid(row=0, column=1, padx=10, pady=10)

        # Tworzenie rozwijanej listy LandType
        land_form_label = tk.Label(self.root, text="Select land form type:")
        land_form_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.land_form_var = tk.StringVar()
        land_form_combobox = ttk.Combobox(
            self.root, 
            textvariable=self.land_form_var, 
            values=[
                "marshes and lowlands",
                "flats and plateaus",
                "flats and plateaus in combination with hills",
                "hills with gentle slopes",
                "steeper hills and foothills",
                "hills and outcrops of mountain ranges",
                "higher hills",
                "mountains",
                "highest mountains",
            ], 
            width=25
            )
        land_form_combobox.grid(row=1, column=1, padx=10, pady=10)

        # Tworzenie pola do wprowadzenia parametru Area
        area_label = tk.Label(self.root, text="Area [ha]:")
        area_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.area_var = tk.StringVar()
        area_entry = tk.Entry(self.root, textvariable=self.area_var, width=28)
        area_entry.grid(row=2, column=1, padx=10, pady=10)

        # Selecting file
        file_label = tk.Label(self.root, text="Select file:")
        file_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        choose_file_button = tk.Button(self.root, text="Select file", command=self.choose_file, width=23)
        choose_file_button.grid(row=3, column=1, padx=10, pady=10)

        # Selected file
        selected_label = tk.Label(self.root, text="Selected file:")
        selected_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")

        self.selected_file_label = tk.Entry(self.root, width=28, state='readonly')
        self.selected_file_label.grid(row=4, column=1, padx=10, pady=10, sticky="w")

        # Tworzenie przycisku Run
        run_label = tk.Label(self.root, text="Run simulation:")
        run_label.grid(row=5, column=0, padx=10, pady=10, sticky="w")

        run_button = tk.Button(self.root, text="Run", command=self.run_simulation, width=23, bg="#36D7B7")
        run_button.grid(row=5, column=1, padx=10, pady=10, sticky="w")

    def choose_file(self):
        file_path = filedialog.askopenfilename(title="Wybierz plik", filetypes=(("Pliki tekstowe", "*.txt"), ("Wszystkie pliki", "*.*")))
        if file_path:
            # Sprawdź, czy plik ma rozszerzenie ".inp"
            file_extension = os.path.splitext(file_path)[1]
            if file_extension.lower() != ".inp":
                messagebox.showerror("Error", "Please select a file with the '.inp' extension.")
                return

            # Aktualizowanie pola tekstowego z nazwą pliku
            self.selected_file_label.config(state='normal')
            self.selected_file_label.delete(0, tk.END)
            self.selected_file_label.insert(0, file_path)
            self.selected_file_label.config(state='readonly')

            self.file_path = file_path

    def run_simulation(self):
        land_cover = self.land_cover_var.get().replace(" ", "_")
        land_form = self.land_form_var.get().replace(" ", "_")
        area = self.area_var.get()

        if not self.file_path:
            messagebox.showerror("Error", "Please select a file.")
            return

        if not land_cover:
            messagebox.showerror("Error", "Please select a value for 'Land cover type'.")
            return

        if not land_form:
            messagebox.showerror("Error", "Please select a value for 'Land form type'.")
            return

        if not area:
            messagebox.showerror("Error", "Please enter a value for the 'Area' parameter.")
            return

        try:
            area = area.replace(",", ".")
            area = float(area)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid value for the 'Area' parameter.")
            return

        generate_subcatchment(self.file_path, area, land_form, land_cover)

        messagebox.showinfo("Information", f"Simulation has been executed successfully for values: \n\nArea: {area}\nLand cover type: {land_cover}\nLand form type: {land_form}\nFile: {self.file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RcgApp(root)
    root.mainloop()
