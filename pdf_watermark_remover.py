import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar, Canvas, Frame, Label, Entry, Scale, Checkbutton, BooleanVar
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import os
import math


class PDFImageRemover(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Object Remover v2.4")
        self.geometry("1200x900")

        # --- State Variables ---
        self.doc = None
        self.filepath = None
        self.current_page_num = 0
        self.tk_img = None
        self.page_objects = []
        self.highlight_rect_id = None
        self.zoom_factor = 1.0
        self.manual_zoom = False
        self.user_zoom_level = 1.0
        self.resize_timer = None
        self.page_var = tk.IntVar(value=1)
        self.remove_all_pages = BooleanVar(value=True)
        self.text_remove_by_location = BooleanVar(value=True)
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False

        # --- GUI Layout ---
        top_frame = Frame(self, bd=2, relief=tk.RAISED)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.upload_button = tk.Button(top_frame, text="Upload PDF", command=self.upload_pdf)
        self.upload_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.remove_button = tk.Button(top_frame, text="Remove Selected Object", command=self.remove_object, state=tk.DISABLED)
        self.remove_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.save_button = tk.Button(top_frame, text="Save As...", command=self.save_as, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Zoom controls
        Label(top_frame, text="Zoom:").pack(side=tk.LEFT, padx=(15, 5))
        self.zoom_slider = Scale(top_frame, from_=10, to=500, orient=tk.HORIZONTAL, command=self.on_zoom_slider_change, showvalue=0, state=tk.DISABLED, length=150)
        self.zoom_slider.set(100)
        self.zoom_slider.pack(side=tk.LEFT, padx=5)
        self.zoom_label = Label(top_frame, text="100%")
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        self.reset_zoom_button = tk.Button(top_frame, text="Reset", command=self.reset_zoom, state=tk.DISABLED)
        self.reset_zoom_button.pack(side=tk.LEFT, padx=5)

        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=8)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        pdf_frame = Frame(main_pane)
        canvas_container = Frame(pdf_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = Canvas(canvas_container, bg="#CCCCCC")
        v_scroll = Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scroll = Scrollbar(canvas_container, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind('<Configure>', self.on_resize)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        self.canvas.bind('<ButtonPress-1>', self.on_canvas_press)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)

        # --- Navigation Controls ---
        nav_container = Frame(pdf_frame, bd=1, relief=tk.RAISED)
        nav_container.pack(side=tk.BOTTOM, fill=tk.X, ipady=5)

        self.prev_button = tk.Button(nav_container, text="< Prev", command=self.prev_page, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=10)
        
        self.page_label = Label(nav_container, text="Page 0 of 0")
        self.page_label.pack(side=tk.LEFT, padx=10)

        self.go_to_entry = Entry(nav_container, width=5, textvariable=self.page_var)
        self.go_to_entry.pack(side=tk.LEFT, padx=(20, 5))
        self.go_to_button = tk.Button(nav_container, text="Go", command=self.go_to_page_from_entry, state=tk.DISABLED)
        self.go_to_button.pack(side=tk.LEFT)
        
        self.next_button = tk.Button(nav_container, text="Next >", command=self.next_page, state=tk.DISABLED)
        self.next_button.pack(side=tk.RIGHT, padx=10)
        
        self.page_slider = Scale(nav_container, from_=1, to=1, orient=tk.HORIZONTAL, command=self.on_slider_change, showvalue=0, state=tk.DISABLED)
        self.page_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=20)
        
        main_pane.add(pdf_frame, width=800)

        right_frame = Frame(main_pane)
        
        # Removal options
        options_frame = Frame(right_frame, bd=2, relief=tk.GROOVE)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        Label(options_frame, text="Removal Options:", font=("Arial", 10, "bold")).pack(anchor="w", padx=5, pady=5)
        Checkbutton(options_frame, text="Remove from all pages", variable=self.remove_all_pages).pack(anchor="w", padx=20)
        Checkbutton(options_frame, text="Text removal by location (unchecked = by content only)", variable=self.text_remove_by_location).pack(anchor="w", padx=20)
        
        Label(right_frame, text="Objects on Current Page:").pack(anchor="w", pady=(10, 0))
        list_container = Frame(right_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        self.objects_listbox = Listbox(list_container)
        self.objects_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar = Scrollbar(list_container, orient="vertical", command=self.objects_listbox.yview)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.objects_listbox.config(yscrollcommand=list_scrollbar.set)
        self.objects_listbox.bind("<<ListboxSelect>>", self.on_object_select)
        main_pane.add(right_frame, width=400)
        
        self.status_bar = Label(self, text="Please upload a PDF to begin.", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def upload_pdf(self):
        filepath = filedialog.askopenfilename(title="Select a PDF", filetypes=[("PDF Files", "*.pdf")])
        if not filepath: return
        try:
            self.doc = fitz.open(filepath)
            if not self.doc.page_count:
                messagebox.showerror("Error", "The selected PDF has no pages.")
                return
            
            self.filepath = filepath
            self.current_page_num = 0
            self.page_slider.config(to=self.doc.page_count, state=tk.NORMAL)
            self.go_to_button.config(state=tk.NORMAL)
            self.zoom_slider.config(state=tk.NORMAL)
            self.reset_zoom_button.config(state=tk.NORMAL)
            self.render_page()
            self.status_bar.config(text=f"Loaded: {os.path.basename(self.filepath)}")
            self.save_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load PDF: {e}")
            self.doc = None

    def render_page(self, page_num=None):
        if page_num is not None: self.current_page_num = page_num
        if not self.doc: return
        
        self.canvas.delete("all")
        self.objects_listbox.delete(0, tk.END)
        self.remove_button.config(state=tk.DISABLED)
        self.highlight_rect_id = None
        
        page = self.doc.load_page(self.current_page_num)
        
        page_rect = page.rect
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            self.after(100, self.render_page)
            return
        
        if self.manual_zoom:
            self.zoom_factor = self.user_zoom_level
        else:
            zoom_x = canvas_width / page_rect.width
            zoom_y = canvas_height / page_rect.height
            self.zoom_factor = min(zoom_x, zoom_y, 1.0)
            self.user_zoom_level = self.zoom_factor
        
        zoom_percent = int(self.zoom_factor * 100)
        self.zoom_label.config(text=f"{zoom_percent}%")
        if not self.manual_zoom:
            self.zoom_slider.set(zoom_percent)
        
        # Update cursor based on zoom state
        if self.manual_zoom:
            self.canvas.config(cursor="hand2")
        else:
            self.canvas.config(cursor="")
        
        mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pix = page.get_pixmap(matrix=mat)
        
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_img = ImageTk.PhotoImage(img)
        
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        self.list_page_objects()
        self.update_nav_controls()

    def list_page_objects(self):
        self.page_objects = []
        if not self.doc: return
        page = self.doc.load_page(self.current_page_num)
        
        images = page.get_images(full=True)
        for i, img_info in enumerate(images):
            bbox = page.get_image_bbox(img_info)
            self.page_objects.append({"type": "image", "bbox": bbox, "xref": img_info[0]})
            self.objects_listbox.insert(tk.END, f"Image {i+1} [ID:{img_info[0]}] | Size: {img_info[2]}x{img_info[3]}")
        
        drawings = page.get_drawings()
        for i, path in enumerate(drawings):
            self.page_objects.append({"type": "vector", "bbox": path["rect"], "path": path})
            self.objects_listbox.insert(tk.END, f"Vector {i+1} | Type: {path['type']}")

        blocks = page.get_text("blocks")
        for i, block in enumerate(blocks):
            if block[6] == 0:
                bbox = fitz.Rect(block[0], block[1], block[2], block[3])
                text_content = block[4].strip()
                if not text_content: continue
                self.page_objects.append({"type": "text", "bbox": bbox, "content": text_content})
                snippet = (text_content[:40] + '...') if len(text_content) > 40 else text_content
                self.objects_listbox.insert(tk.END, f"Text {i+1} | \"{snippet.replace(chr(10), ' ')}\"")

    def on_object_select(self, event):
        selection = self.objects_listbox.curselection()
        if not selection: return
        obj = self.page_objects[selection[0]]
        bbox = obj["bbox"]
        if self.highlight_rect_id: self.canvas.delete(self.highlight_rect_id)
        scaled_bbox = (bbox.x0 * self.zoom_factor, bbox.y0 * self.zoom_factor, bbox.x1 * self.zoom_factor, bbox.y1 * self.zoom_factor)
        self.highlight_rect_id = self.canvas.create_rectangle(scaled_bbox, outline="red", width=3)
        self.remove_button.config(state=tk.NORMAL if obj.get('type') in ['image', 'text'] else tk.DISABLED)

    def remove_object(self):
        selection = self.objects_listbox.curselection()
        if not selection: return
        obj = self.page_objects[selection[0]]
        obj_type = obj.get('type')

        if obj_type == 'image':
            self.remove_image_by_xref(obj)
        elif obj_type == 'text':
            if self.text_remove_by_location.get():
                self.remove_text_by_location(obj)
            else:
                self.remove_text_by_content(obj)
        else:
            messagebox.showinfo("Not Supported", f"Removal of '{obj_type}' objects is not yet supported.")
    
    def remove_image_by_xref(self, obj):
        target_xref = obj.get('xref')
        if not target_xref: return
        
        remove_all = self.remove_all_pages.get()
        scope = "all pages" if remove_all else "current page only"
        if not messagebox.askyesno("Confirm Image Deletion", f"Remove Image ID {target_xref} from {scope}?"): return
        
        try:
            images_deleted = 0
            if remove_all:
                for page in self.doc:
                    if page.delete_image(target_xref): images_deleted += 1
            else:
                page = self.doc.load_page(self.current_page_num)
                if page.delete_image(target_xref): images_deleted = 1
            
            self.status_bar.config(text=f"Deleted {images_deleted} image instance(s). Remember to 'Save As...'")
            messagebox.showinfo("Success", f"{images_deleted} instance(s) marked for deletion. Save the file.")
            self.render_page()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during image deletion: {e}")

    def remove_text_by_location(self, obj):
        target_bbox, target_content = obj.get('bbox'), obj.get('content', '').strip()
        if not target_bbox or not target_content: return
        snippet = (target_content[:30] + '...') if len(target_content) > 30 else target_content
        
        remove_all = self.remove_all_pages.get()
        scope = "ALL pages" if remove_all else "current page only"
        msg = f"Permanently REMOVE text matching:\n\nContent: \"{snippet}\"\nLocation: Near this area\n\nFrom {scope}?"
        if not messagebox.askyesno("Confirm Text Removal by Location", msg): return
        
        try:
            removed_count = 0
            tolerance = 2.0
            pages_to_process = self.doc if remove_all else [self.doc.load_page(self.current_page_num)]
            
            for page in pages_to_process:
                blocks = page.get_text("blocks")
                for block in blocks:
                    if block[6] == 0 and block[4].strip() == target_content:
                        current_bbox = fitz.Rect(block[:4])
                        if math.isclose(current_bbox.x0, target_bbox.x0, abs_tol=tolerance) and math.isclose(current_bbox.y0, target_bbox.y0, abs_tol=tolerance):
                            page.add_redact_annot(current_bbox)
                            removed_count += 1
            
            if removed_count == 0:
                messagebox.showinfo("No Matches", "No matching text blocks were found.")
                return
            
            for page in pages_to_process:
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
            
            self.status_bar.config(text=f"Removed {removed_count} text instance(s). Remember to 'Save As...'")
            messagebox.showinfo("Success", f"{removed_count} instance(s) removed. Save the file.")
            self.render_page()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during text removal: {e}")

    def remove_text_by_content(self, obj):
        target_content = obj.get('content', '').strip()
        if not target_content: return
        snippet = (target_content[:40] + '...') if len(target_content) > 40 else target_content
        
        remove_all = self.remove_all_pages.get()
        scope = "the ENTIRE PDF" if remove_all else "current page only"
        msg = f"Permanently REMOVE all occurrences of the text \"{snippet}\" from {scope}, regardless of location?"
        if not messagebox.askyesno("Confirm Text Removal by Content", msg): return

        try:
            removed_count = 0
            pages_to_process = self.doc if remove_all else [self.doc.load_page(self.current_page_num)]
            
            for page in pages_to_process:
                areas = page.search_for(target_content)
                for area in areas:
                    page.add_redact_annot(area)
                    removed_count += 1
            
            if removed_count == 0:
                messagebox.showinfo("No Matches", "That text was not found.")
                return
            
            for page in pages_to_process:
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
            
            self.status_bar.config(text=f"Removed {removed_count} text instance(s). Remember to 'Save As...'")
            messagebox.showinfo("Success", f"{removed_count} instance(s) of the text were removed. Save the file.")
            self.render_page()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during text removal: {e}")

    def save_as(self):
        if not self.doc: return
        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")], title="Save Modified PDF As...")
        if not output_path: return
        try:
            self.doc.save(output_path, garbage=4, deflate=True, clean=True)
            self.status_bar.config(text=f"File saved successfully to {output_path}")
            messagebox.showinfo("Saved", f"Modified PDF saved to:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save the file: {e}")
            
    def next_page(self):
        if self.doc and self.current_page_num < self.doc.page_count - 1:
            self.render_page(self.current_page_num + 1)

    def prev_page(self):
        if self.doc and self.current_page_num > 0:
            self.render_page(self.current_page_num - 1)

    def go_to_page_from_entry(self):
        if not self.doc: return
        try:
            page_num = int(self.go_to_entry.get()) - 1
            if 0 <= page_num < self.doc.page_count:
                self.render_page(page_num)
            else:
                self.status_bar.config(text=f"Invalid page number. Must be between 1 and {self.doc.page_count}.")
                self.page_var.set(self.current_page_num + 1)
        except ValueError:
            self.status_bar.config(text="Please enter a valid number.")
            self.page_var.set(self.current_page_num + 1)
            
    def on_slider_change(self, value):
        if self.doc and int(value) - 1 != self.current_page_num:
            self.render_page(int(value) - 1)

    def update_nav_controls(self):
        if not self.doc: return
        self.page_label.config(text=f"of {self.doc.page_count}")
        self.page_var.set(self.current_page_num + 1)
        self.page_slider.set(self.current_page_num + 1)
        self.prev_button.config(state=tk.NORMAL if self.current_page_num > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_page_num < self.doc.page_count - 1 else tk.DISABLED)

    def on_resize(self, event):
        if self.resize_timer: self.after_cancel(self.resize_timer)
        if not self.manual_zoom:
            self.resize_timer = self.after(250, self.render_page)
    
    def on_zoom_slider_change(self, value):
        if not self.doc: return
        self.manual_zoom = True
        self.user_zoom_level = int(value) / 100.0
        self.render_page()
    
    def on_mouse_wheel(self, event):
        if not self.doc: return
        if self.manual_zoom:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            if event.delta > 0:
                self.prev_page()
            else:
                self.next_page()
    
    def on_canvas_press(self, event):
        if not self.doc or not self.manual_zoom: return
        self.is_dragging = True
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.config(cursor="fleur")
    
    def on_canvas_drag(self, event):
        if not self.is_dragging: return
        self.canvas.scan_dragto(event.x, event.y, gain=1)
    
    def on_canvas_release(self, event):
        if not self.is_dragging: return
        self.is_dragging = False
        if self.manual_zoom:
            self.canvas.config(cursor="hand2")
    
    def reset_zoom(self):
        if not self.doc: return
        self.manual_zoom = False
        self.render_page()

if __name__ == "__main__":
    app = PDFImageRemover()
    app.mainloop()

