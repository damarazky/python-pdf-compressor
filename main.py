import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import scrolledtext
import threading
import subprocess
import tempfile
from pathlib import Path

class PDFCompressor:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Compressor - Under 5 MB")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Variables
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.compression_level = tk.StringVar(value="medium")
        self.status_text = tk.StringVar(value="Ready")
        self.is_compressing = False
        
        # Create GUI
        self.create_widgets()
        
        # Check dependencies
        self.check_dependencies()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="PDF Compressor", 
                                font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Input file selection
        input_frame = ttk.LabelFrame(main_frame, text="Input PDF File", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="File Path:").grid(row=0, column=0, sticky=tk.W)
        
        input_entry = ttk.Entry(input_frame, textvariable=self.input_path, width=50)
        input_entry.grid(row=0, column=1, padx=5)
        
        browse_input_btn = ttk.Button(input_frame, text="Browse", 
                                      command=self.browse_input)
        browse_input_btn.grid(row=0, column=2, padx=5)
        
        # Output file selection
        output_frame = ttk.LabelFrame(main_frame, text="Output PDF File", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="Save As:").grid(row=0, column=0, sticky=tk.W)
        
        output_entry = ttk.Entry(output_frame, textvariable=self.output_path, width=50)
        output_entry.grid(row=0, column=1, padx=5)
        
        browse_output_btn = ttk.Button(output_frame, text="Browse", 
                                       command=self.browse_output)
        browse_output_btn.grid(row=0, column=2, padx=5)
        
        # Compression settings
        settings_frame = ttk.LabelFrame(main_frame, text="Compression Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # Compression level
        ttk.Label(settings_frame, text="Compression Level:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        level_frame = ttk.Frame(settings_frame)
        level_frame.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        ttk.Radiobutton(level_frame, text="Low (Faster)", 
                        variable=self.compression_level, value="low").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(level_frame, text="Medium (Balanced)", 
                        variable=self.compression_level, value="medium").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(level_frame, text="High (More Compression)", 
                        variable=self.compression_level, value="high").pack(side=tk.LEFT, padx=5)
        
        # Target size info
        ttk.Label(settings_frame, text="Target Size: Under 5 MB", 
                  font=('Arial', 10, 'bold')).grid(row=1, column=0, columnspan=2, pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=400)
        self.progress.pack(pady=10, fill=tk.X)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        self.compress_btn = ttk.Button(button_frame, text="Compress PDF", 
                                       command=self.start_compression, width=20)
        self.compress_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Clear", 
                  command=self.clear_fields, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Exit", 
                  command=self.root.quit, width=15).pack(side=tk.LEFT, padx=5)
        
        # Status
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        ttk.Label(status_frame, textvariable=self.status_text, 
                  font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, 
                                                  wrap=tk.WORD, state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('success', foreground='green')
        self.log_text.tag_config('info', foreground='blue')
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        required_packages = {
        'pypdf': 'pypdf',
        'PIL': 'Pillow',
        'reportlab': 'reportlab'
    }
        missing = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        
        if missing:
            self.log_message(f"Missing dependencies: {', '.join(missing)}", 'error')
            self.log_message("Please install them using: pip install " + ' '.join(missing), 'error')
        else:
            self.log_message("All dependencies installed ✓", 'success')
        
        # Check Ghostscript
        gs_path = self.find_ghostscript()
        if gs_path:
            self.log_message(f"Ghostscript found: {gs_path} ✓", 'success')
        else:
            self.log_message("Ghostscript not found. Using PyPDF2 only (limited compression)", 'error')
    
    def find_ghostscript(self):
        """Find Ghostscript executable in system"""
        # Common Ghostscript executable names
        gs_commands = ['gs', 'gswin64c', 'gswin64', 'gswin32c']
        
        # Common installation paths for Windows
        common_paths = [
            r"D:\gs10.07.1\bin\gswin64c.exe",
            r"D:\gs10.07.1\bin\gswin64.exe",
            r"D:\gs10.07.1\bin\gswin32c.exe",
            r"D:\gs10.07.1\bin\gswin64c.exe",
        ]
        
        # Try commands in PATH first
        for cmd in gs_commands:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, 
                                      check=True,
                                      timeout=2,
                                      shell=True)
                if result.returncode == 0:
                    return cmd
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        # Try common installation paths
        import glob
        for path_pattern in common_paths:
            matches = glob.glob(path_pattern)
            if matches:
                # Get the latest version
                matches.sort(reverse=True)
                return matches[0]
        
        return None
    
    def log_message(self, message, tag='info'):
        """Add message to log area"""
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')
        self.root.update()
    
    def browse_input(self):
        """Browse for input PDF file"""
        filename = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.input_path.set(filename)
            # Auto-generate output path
            if not self.output_path.get():
                base = os.path.splitext(filename)[0]
                self.output_path.set(f"{base}_compressed.pdf")
    
    def browse_output(self):
        """Browse for output PDF file"""
        filename = filedialog.asksaveasfilename(
            title="Save Compressed PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if filename:
            self.output_path.set(filename)
    
    def clear_fields(self):
        """Clear all fields"""
        self.input_path.set("")
        self.output_path.set("")
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
        self.status_text.set("Ready")
        self.progress.stop()
    
    def start_compression(self):
        """Start compression in a separate thread"""
        if self.is_compressing:
            messagebox.showwarning("Warning", "Compression already in progress!")
            return
        
        if not self.input_path.get():
            messagebox.showerror("Error", "Please select an input PDF file!")
            return
        
        if not os.path.exists(self.input_path.get()):
            messagebox.showerror("Error", "Input file does not exist!")
            return
        
        if not self.output_path.get():
            messagebox.showerror("Error", "Please specify an output file path!")
            return
        
        # Disable compress button during operation
        self.compress_btn.configure(state='disabled')
        self.is_compressing = True
        self.status_text.set("Compressing...")
        self.progress.start()
        
        # Run compression in thread
        thread = threading.Thread(target=self.compress_pdf)
        thread.daemon = True
        thread.start()
    
    def compress_pdf(self):
        """Main compression function"""
        try:
            input_file = self.input_path.get()
            output_file = self.output_path.get()
            level = self.compression_level.get()
            
            # Check file size
            original_size = os.path.getsize(input_file) / (1024 * 1024)  # MB
            self.log_message(f"Original file size: {original_size:.2f} MB", 'info')
            
            if original_size <= 5:
                self.log_message("File already under 5 MB", 'info')
                self.root.after(0, lambda: self.show_completion(original_size))
                return
            
            # Set compression quality based on level
            quality_map = {
                'low': 90,
                'medium': 75,
                'high': 50
            }
            
            quality = quality_map.get(level, 75)
            self.log_message(f"Starting compression with quality: {quality}%", 'info')
            
            # Try using Ghostscript first (better compression)
            gs_path = self.find_ghostscript()
            success = False
            
            if gs_path:
                self.log_message(f"Using Ghostscript for compression", 'info')
                success = self.compress_with_ghostscript(input_file, output_file, quality, gs_path)
            else:
                self.log_message("Ghostscript not available, using PyPDF2", 'info')
                success = self.compress_with_pypdf(input_file, output_file, quality)
            
            # Check result
            if success and os.path.exists(output_file):
                compressed_size = os.path.getsize(output_file) / (1024 * 1024)
                self.log_message(f"Compressed file size: {compressed_size:.2f} MB", 'info')
                
                if compressed_size <= 5:
                    self.log_message(f"✓ Success! File compressed to under 5 MB", 'success')
                    self.log_message(f"Saved to: {output_file}", 'success')
                    self.root.after(0, lambda: self.show_completion(original_size, compressed_size))
                else:
                    self.log_message(f"File size still above 5 MB ({compressed_size:.2f} MB)", 'error')
                    self.log_message("Attempting aggressive compression...", 'info')
                    
                    # Try aggressive compression with Ghostscript
                    if gs_path:
                        aggressive_success = self.compress_with_ghostscript(input_file, output_file, 30, gs_path)
                        if aggressive_success:
                            new_size = os.path.getsize(output_file) / (1024 * 1024)
                            self.log_message(f"New size: {new_size:.2f} MB", 'info')
                            if new_size <= 5:
                                self.log_message("✓ Success with aggressive compression!", 'success')
                                self.root.after(0, lambda: self.show_completion(original_size, new_size))
                            else:
                                self.log_message("File remains above 5 MB. Consider reducing content manually.", 'error')
                    else:
                        self.log_message("Cannot compress further without Ghostscript", 'error')
            else:
                self.log_message("Compression failed. Please ensure the file is valid.", 'error')
        
        except Exception as e:
            self.log_message(f"Error during compression: {str(e)}", 'error')
        
        finally:
            # Re-enable controls
            self.root.after(0, self.enable_controls)
    
    def compress_with_pypdf(self, input_file, output_file, quality):
        """Compress PDF using PyPDF2"""
        try:
            from PyPDF2 import PdfReader, PdfWriter
            
            reader = PdfReader(input_file)
            writer = PdfWriter()
            
            # Copy pages with compression
            for page in reader.pages:
                writer.add_page(page)
            
            # Set compression based on quality
            if quality <= 50:
                writer.compress_content_streams = True
            
            # Try to reduce size by removing metadata
            writer.add_metadata({})
            
            # Write output
            with open(output_file, 'wb') as f:
                writer.write(f)
            
            return True
        except Exception as e:
            self.log_message(f"PyPDF2 compression failed: {str(e)}", 'error')
            return False
    
    def compress_with_ghostscript(self, input_file, output_file, quality, gs_path):
        """Compress PDF using Ghostscript"""
        try:
            # Pilih setting berdasarkan quality
            if quality >= 75:
                gs_setting = '/printer'      # Kualitas tinggi, ukuran sedang
                resolution = 150
            elif quality >= 50:
                gs_setting = '/ebook'        # Kualitas sedang, ukuran kecil
                resolution = 100
            else:
                gs_setting = '/screen'       # Kualitas rendah, ukuran sangat kecil
                resolution = 72
            
            # Build Ghostscript command with aggressive compression
            cmd = [
                gs_path,
                '-sDEVICE=pdfwrite',
                '-dCompatibilityLevel=1.4',
                f'-dPDFSETTINGS={gs_setting}',
                '-dNOPAUSE',
                '-dQUIET',
                '-dBATCH',
                '-dSAFER',
                '-dAutoRotatePages=/None',
                f'-dColorImageResolution={resolution}',
                f'-dGrayImageResolution={resolution}',
                f'-dMonoImageResolution={resolution}',
                '-dDownsampleColorImages=true',
                '-dDownsampleGrayImages=true',
                '-dDownsampleMonoImages=true',
                '-dColorImageDownsampleType=/Bicubic',
                '-dGrayImageDownsampleType=/Bicubic',
                '-dMonoImageDownsampleType=/Bicubic',
                '-dColorImageDict=/QFactor 0.1/Blend 1',
                '-dGrayImageDict=/QFactor 0.1/Blend 1',
                '-dMonoImageDict=/QFactor 0.1/Blend 1',
                '-dOptimize=true',
                '-dUseCIEColor=false',
                '-dSubsetFonts=true',
                '-dEmbedAllFonts=false',
                f'-sOutputFile={output_file}',
                input_file
            ]
            
            self.log_message(f"Running Ghostscript with setting: {gs_setting} (resolution: {resolution})", 'info')
            
            # Run Ghostscript
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                self.log_message(f"Ghostscript error: {result.stderr}", 'error')
                return False
            
            # Verify output exists and has content
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                return True
            else:
                self.log_message("Ghostscript output file is empty or missing", 'error')
                return False
            
        except subprocess.TimeoutExpired:
            self.log_message("Ghostscript compression timed out (5 minutes)", 'error')
            return False
        except Exception as e:
            self.log_message(f"Ghostscript compression failed: {str(e)}", 'error')
            return False
    
    def show_completion(self, original_size, compressed_size=None):
        """Show completion message"""
        if compressed_size is None:
            message = f"File already under 5 MB!\n\nOriginal: {original_size:.2f} MB"
        else:
            reduction = ((original_size - compressed_size) / original_size) * 100
            message = f"Compression completed!\n\n" \
                     f"Original: {original_size:.2f} MB\n" \
                     f"Compressed: {compressed_size:.2f} MB\n" \
                     f"Reduction: {reduction:.1f}%"
        
        messagebox.showinfo("Success", message)
    
    def enable_controls(self):
        """Re-enable controls after compression"""
        self.is_compressing = False
        self.compress_btn.configure(state='normal')
        self.status_text.set("Ready")
        self.progress.stop()

def main():
    root = tk.Tk()
    app = PDFCompressor(root)
    
    try:
        root.iconbitmap(default='icon.ico')
    except:
        pass
    
    root.mainloop()

if __name__ == "__main__":
    main()