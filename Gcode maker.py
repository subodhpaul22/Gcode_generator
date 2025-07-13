import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from svgpathtools import svg2paths
import os

def generate_gcode(svg_file, tool_type, user_max_x, user_max_y):
    try:
        paths, _ = svg2paths(svg_file)

        # SVG bounding box
        min_x, min_y = float('inf'), float('inf')
        max_x_svg, max_y_svg = float('-inf'), float('-inf')

        for path in paths:
            for segment in path:
                xs = [segment.start.real, segment.end.real]
                ys = [segment.start.imag, segment.end.imag]
                min_x = min(min_x, *xs)
                max_x_svg = max(max_x_svg, *xs)
                min_y = min(min_y, *ys)
                max_y_svg = max(max_y_svg, *ys)

        width_svg = max_x_svg - min_x
        height_svg = max_y_svg - min_y

        if width_svg == 0 or height_svg == 0:
            raise ValueError("SVG has zero width or height!")

        # Calculate scale factors separately for x and y
        scale_x = user_max_x / width_svg
        scale_y = user_max_y / height_svg

        # Use separate scales on X and Y axes (no forced aspect ratio)
        # So width will become width_svg*scale_x and height become height_svg*scale_y

        gcode = []
        gcode.append("G21 ; Set units to mm")
        gcode.append("G90 ; Absolute positioning")

        if tool_type == "Servo":
            gcode.append("M3 S90 ; Servo Pen Down")
        else:
            gcode.append("M3 ; Spindle On")

        for path in paths:
            start = path[0].start
            sx = (start.real - min_x) * scale_x
            sy = (max_y_svg - start.imag) * scale_y  # Flip Y axis

            gcode.append(f"G0 X{sx:.2f} Y{sy:.2f} ; Move to start")

            for segment in path:
                ex = (segment.end.real - min_x) * scale_x
                ey = (max_y_svg - segment.end.imag) * scale_y  # Flip Y axis
                gcode.append(f"G1 X{ex:.2f} Y{ey:.2f}")

        if tool_type == "Servo":
            gcode.append("M5 ; Servo Pen Up")
        else:
            gcode.append("M5 ; Spindle Off")

        return "\n".join(gcode)

    except Exception as e:
        messagebox.showerror("Error", f"G-code generation failed:\n{e}")
        return ""

def load_svg():
    file_path = filedialog.askopenfilename(filetypes=[("SVG Files", "*.svg")])
    if file_path:
        svg_path.set(file_path)
        label_file.config(text=os.path.basename(file_path))

def convert_and_save():
    svg_file = svg_path.get()
    tool_type = tool_var.get()

    if not svg_file:
        messagebox.showwarning("No file", "Please load an SVG file first.")
        return

    try:
        max_x_val = float(max_x.get())
        max_y_val = float(max_y.get())
        if max_x_val <= 0 or max_y_val <= 0:
            raise ValueError
    except:
        messagebox.showerror("Invalid Input", "Please enter valid positive numbers for max X and max Y.")
        return

    gcode = generate_gcode(svg_file, tool_type, max_x_val, max_y_val)

    if gcode:
        save_path = filedialog.asksaveasfilename(defaultextension=".gcode",
                                                 filetypes=[("G-code files", "*.gcode")])
        if save_path:
            with open(save_path, "w") as f:
                f.write(gcode)
            messagebox.showinfo("Saved", f"G-code saved to:\n{save_path}")

root = tk.Tk()
root.title("SVG to G-code Converter (Non-uniform scale)")
root.geometry("500x420")
root.resizable(False, False)

svg_path = tk.StringVar()
tool_var = tk.StringVar(value="Stepper")
max_x = tk.StringVar(value="1000.0")
max_y = tk.StringVar(value="500.0")

tk.Label(root, text="SVG File:").pack(pady=5)
tk.Entry(root, textvariable=svg_path, width=60).pack(padx=10)
tk.Button(root, text="Browse SVG", command=load_svg).pack(pady=5)

label_file = tk.Label(root, text="No file selected", fg="blue")
label_file.pack()

tk.Label(root, text="Select Tool Type:").pack(pady=10)
ttk.Combobox(root, textvariable=tool_var, values=["Stepper", "Servo"], state="readonly").pack()

tk.Label(root, text="Width (X mm):").pack(pady=5)
tk.Entry(root, textvariable=max_x, width=10, justify="center").pack()

tk.Label(root, text="Height (Y mm):").pack(pady=5)
tk.Entry(root, textvariable=max_y, width=10, justify="center").pack()

tk.Button(root, text="Convert to G-code & Save", command=convert_and_save,
          bg="green", fg="white", padx=10, pady=5).pack(pady=20)

root.mainloop()
