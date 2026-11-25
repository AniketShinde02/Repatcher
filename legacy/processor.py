import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageDraw

class ImageProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aniket.Work — Safe Image Processor")
        self.root.geometry("650x550")
        self.root.minsize(550, 480)
        
        # Style configurations
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TButton", padding=6, font=("Helvetica", 10))
        self.style.configure("Primary.TButton", background="#18A558", foreground="white", font=("Helvetica", 10, "bold"))
        self.style.map("Primary.TButton", background=[("active", "#128243")])
        self.style.configure("Danger.TButton", background="#d9534f", foreground="white", font=("Helvetica", 10))
        self.style.map("Danger.TButton", background=[("active", "#c9302c")])
        
        # Default Paths (relative to script location)
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.input_dir = tk.StringVar(value=os.path.join(self.base_dir, "input_images"))
        self.backup_dir = tk.StringVar(value=os.path.join(self.base_dir, "backup_images"))
        self.output_dir = tk.StringVar(value=os.path.join(self.base_dir, "cleaned_images"))
        
        # Ensure default directories exist
        for path in [self.input_dir.get(), self.backup_dir.get(), self.output_dir.get()]:
            os.makedirs(path, exist_ok=True)
            
        # Variables
        self.mode = tk.StringVar(value="crop") # "crop" or "fill"
        self.crop_height = tk.IntVar(value=80)
        self.fill_width = tk.IntVar(value=80)
        self.fill_height = tk.IntVar(value=80)
        self.auto_backup = tk.BooleanVar(value=True)
        
        self.create_widgets()
        
    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#111111", padx=15, pady=15)
        header_frame.pack(fill="x", side="top")
        
        title_label = tk.Label(header_frame, text="ANIKET.WORK", font=("Helvetica", 14, "bold"), fg="#18A558", bg="#111111")
        title_label.pack(side="left")
        
        subtitle_label = tk.Label(header_frame, text="— Image Processing Sandbox", font=("Helvetica", 11), fg="#FFFFFF", bg="#111111")
        subtitle_label.pack(side="left", padx=5)
        
        # Main Container
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # 1. Folder Selection Frame
        folders_frame = tk.LabelFrame(main_frame, text=" Folder Paths ", font=("Helvetica", 10, "bold"), padx=10, pady=10)
        folders_frame.pack(fill="x", pady=5)
        
        # Input Path
        tk.Label(folders_frame, text="Input Folder:").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(folders_frame, textvariable=self.input_dir, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(folders_frame, text="Browse", command=lambda: self.browse_folder(self.input_dir)).grid(row=0, column=2, padx=2)
        
        # Backup Path
        tk.Label(folders_frame, text="Backup Folder:").grid(row=1, column=0, sticky="w", pady=5)
        tk.Entry(folders_frame, textvariable=self.backup_dir, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(folders_frame, text="Browse", command=lambda: self.browse_folder(self.backup_dir)).grid(row=1, column=2, padx=2)
        
        # Output Path
        tk.Label(folders_frame, text="Output Folder:").grid(row=2, column=0, sticky="w", pady=5)
        tk.Entry(folders_frame, textvariable=self.output_dir, width=50).grid(row=2, column=1, padx=5)
        ttk.Button(folders_frame, text="Browse", command=lambda: self.browse_folder(self.output_dir)).grid(row=2, column=2, padx=2)
        
        # 2. Options Frame
        options_frame = tk.LabelFrame(main_frame, text=" Processing Strategy ", font=("Helvetica", 10, "bold"), padx=10, pady=10)
        options_frame.pack(fill="x", pady=10)
        
        # Radio Selection for Mode
        mode_frame = tk.Frame(options_frame)
        mode_frame.pack(fill="x", pady=5)
        
        tk.Label(mode_frame, text="Select Mode:", font=("Helvetica", 10, "bold")).pack(side="left", padx=(0, 10))
        tk.Radiobutton(mode_frame, text="Trim Bottom Strip (Cleanest)", variable=self.mode, value="crop", command=self.toggle_sliders).pack(side="left", padx=10)
        tk.Radiobutton(mode_frame, text="Solid Color Patch (Fill Corner)", variable=self.mode, value="fill", command=self.toggle_sliders).pack(side="left", padx=10)
        
        # Sliders
        self.slider_frame = tk.Frame(options_frame)
        self.slider_frame.pack(fill="x", pady=10)
        
        # Crop Slider
        self.crop_label = tk.Label(self.slider_frame, text=f"Height to Trim (px): {self.crop_height.get()}")
        self.crop_label.pack(anchor="w")
        self.crop_scale = ttk.Scale(self.slider_frame, from_=5, to=300, variable=self.crop_height, orient="horizontal", command=self.update_crop_label)
        self.crop_scale.pack(fill="x", pady=5)
        
        # Fill Dimension Sliders (Hidden by default)
        self.fill_w_label = tk.Label(self.slider_frame, text=f"Patch Width (px): {self.fill_width.get()}")
        self.fill_h_label = tk.Label(self.slider_frame, text=f"Patch Height (px): {self.fill_height.get()}")
        self.fill_w_scale = ttk.Scale(self.slider_frame, from_=10, to=300, variable=self.fill_width, orient="horizontal", command=self.update_fill_label)
        self.fill_h_scale = ttk.Scale(self.slider_frame, from_=10, to=300, variable=self.fill_height, orient="horizontal", command=self.update_fill_label)
        
        self.toggle_sliders() # Initial view setup
        
        # 3. Execution & Safety Frame
        exec_frame = tk.Frame(main_frame)
        exec_frame.pack(fill="x", pady=10)
        
        # Auto Backup checkbox
        tk.Checkbutton(exec_frame, text="Automatically backup original images before running", variable=self.auto_backup).pack(anchor="w", pady=5)
        
        # Process Button
        self.btn_process = ttk.Button(exec_frame, text="⚡ Run Batch Process", style="Primary.TButton", command=self.run_process)
        self.btn_process.pack(side="left", fill="x", expand=True, padx=5)
        
        # Restore Backup Button
        self.btn_restore = ttk.Button(exec_frame, text="↩️ Restore Originals from Backup", style="Danger.TButton", command=self.restore_backup)
        self.btn_restore.pack(side="right", fill="x", expand=True, padx=5)
        
        # Status Bar
        self.status = tk.StringVar(value="Status: Ready. Place images in the 'input_images' folder.")
        status_bar = tk.Label(self.root, textvariable=self.status, bd=1, relief="sunken", anchor="w", font=("Helvetica", 9), padx=10, pady=5)
        status_bar.pack(side="bottom", fill="x")
        
    def update_crop_label(self, val):
        self.crop_label.config(text=f"Height to Trim (px): {int(float(val))}")
        
    def update_fill_label(self, val):
        self.fill_w_label.config(text=f"Patch Width (px): {int(self.fill_width.get())}")
        self.fill_h_label.config(text=f"Patch Height (px): {int(self.fill_height.get())}")
        
    def toggle_sliders(self):
        if self.mode.get() == "crop":
            self.fill_w_label.pack_forget()
            self.fill_w_scale.pack_forget()
            self.fill_h_label.pack_forget()
            self.fill_h_scale.pack_forget()
            
            self.crop_label.pack(anchor="w")
            self.crop_scale.pack(fill="x", pady=5)
        else:
            self.crop_label.pack_forget()
            self.crop_scale.pack_forget()
            
            self.fill_w_label.pack(anchor="w")
            self.fill_w_scale.pack(fill="x", pady=2)
            self.fill_h_label.pack(anchor="w")
            self.fill_h_scale.pack(fill="x", pady=2)
            
    def browse_folder(self, var):
        folder = filedialog.askdirectory()
        if folder:
            var.set(folder)
            
    def run_process(self):
        input_path = self.input_dir.get()
        backup_path = self.backup_dir.get()
        output_path = self.output_dir.get()
        
        if not os.path.exists(input_path):
            messagebox.showerror("Error", "Input folder does not exist!")
            return
            
        files = [f for f in os.listdir(input_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        if not files:
            messagebox.showinfo("No Images", "No images (.png, .jpg, .jpeg, .webp) found in the Input folder.")
            return
            
        # 1. Execute Backup
        if self.auto_backup.get():
            self.status.set("Status: Creating backups of original images...")
            self.root.update_idletasks()
            for filename in files:
                src = os.path.join(input_path, filename)
                dest = os.path.join(backup_path, filename)
                shutil.copy2(src, dest)
                
        # 2. Execute Processing
        self.status.set(f"Status: Processing {len(files)} images...")
        self.root.update_idletasks()
        
        processed_count = 0
        error_count = 0
        
        for filename in files:
            try:
                img_path = os.path.join(input_path, filename)
                img = Image.open(img_path)
                
                if self.mode.get() == "crop":
                    # Mode: Crop bottom strip
                    width, height = img.size
                    trim_h = self.crop_height.get()
                    if trim_h >= height:
                        raise ValueError(f"Trim height ({trim_h}px) is larger than image height ({height}px)")
                    processed_img = img.crop((0, 0, width, height - trim_h))
                else:
                    # Mode: Solid Color Patch (Fill Corner)
                    width, height = img.size
                    w_box = self.fill_width.get()
                    h_box = self.fill_height.get()
                    
                    if w_box >= width or h_box >= height:
                        raise ValueError("Patch box dimensions are larger than image dimensions")
                    
                    x0 = width - w_box
                    y0 = height - h_box
                    
                    # Sample color from slightly above and left of the patch boundary
                    sample_x = max(0, x0 - 5)
                    sample_y = max(0, y0 - 5)
                    sampled_color = img.getpixel((sample_x, sample_y))
                    
                    # Draw solid block over the watermark
                    processed_img = img.copy()
                    draw = ImageDraw.Draw(processed_img)
                    draw.rectangle([x0, y0, width, height], fill=sampled_color)
                
                # Save to output folder
                out_path = os.path.join(output_path, filename)
                processed_img.save(out_path, quality=95)
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                error_count += 1
                
        self.status.set(f"Status: Processing complete. Succeeded: {processed_count}, Failed: {error_count}.")
        messagebox.showinfo("Success", f"Processed {processed_count} images successfully!\nSaved to: {output_path}")
        
    def restore_backup(self):
        input_path = self.input_dir.get()
        backup_path = self.backup_dir.get()
        
        if not os.path.exists(backup_path):
            messagebox.showerror("Error", "Backup folder does not exist!")
            return
            
        backup_files = [f for f in os.listdir(backup_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        if not backup_files:
            messagebox.showinfo("Empty Backup", "No backed-up images found to restore.")
            return
            
        confirm = messagebox.askyesno("Confirm Restore", "Are you sure you want to restore original images? This will overwrite existing files in your input folder.")
        if not confirm:
            return
            
        self.status.set("Status: Restoring files from backup...")
        self.root.update_idletasks()
        
        restore_count = 0
        for filename in backup_files:
            src = os.path.join(backup_path, filename)
            dest = os.path.join(input_path, filename)
            shutil.copy2(src, dest)
            restore_count += 1
            
        self.status.set(f"Status: Restored {restore_count} images successfully.")
        messagebox.showinfo("Restored", f"Successfully restored {restore_count} original images to the input folder.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageProcessorApp(root)
    root.mainloop()
