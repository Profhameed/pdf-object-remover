import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar, Canvas, Frame, Label, Entry, Scale
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import os
import math

class TextRemoveDialog(tk.Toplevel):
    """Custom dialog to choose the text removal method."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Choose Text Removal Method")
        self.geometry("400x150")
        self.transient(parent)
        self.grab_set()
        self.result = None

        Label(self, text="How should this text be removed?", pady=10).pack()

        btn_frame = Frame(self)
        btn_frame.pack(pady=10, fill="x", expand=True)

        by_location_btn = tk.Button(btn_frame, text="By Location & Content (All Pages)", command=lambda: self.set_choice("location"))
        by_location_btn.pack(pady=5, padx=20, fill="x")

        by_content_btn = tk.Button(btn_frame, text="By Content Only (Entire PDF)", command=lambda: self.set_choice("content"))
        by_content_btn.pack(pady=5, padx=20, fill="x")
        
        self.wait_window(self)

    def set_choice(self, choice):
        self.result = choice
        self.destroy()

class PDFImageRemover(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Object Remover v2.3")
        self.geometry("1200x900")

        # --- State Variables ---
        self.doc = None
        self.filepath = None
        self.current_page_num = 0
        self.tk_img = None
        self.page_objects = []
        self.highlight_rect_id = None
        self.zoom_factor = 1.0
        self.resize_timer = None
        self.page_var = tk.IntVar(value=1)

        # --- GUI Layout ---
        top_frame = Frame(self, bd=2, relief=tk.RAISED)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.upload_button = tk.Button(top_frame, text="Upload PDF", command=self.upload_pdf)
        self.upload_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.remove_button = tk.Button(top_frame, text="Remove Selected Object", command=self.remove_object, state=tk.DISABLED)
        self.remove_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.save_button = tk.Button(top_frame, text="Save As...", command=self.save_as, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)

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
        Label(right_frame, text="Objects on Current Page:").pack(anchor="w")
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
            
        zoom_x = canvas_width / page_rect.width
        zoom_y = canvas_height / page_rect.height
        self.zoom_factor = min(zoom_x, zoom_y, 1.0)
        
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
            dialog = TextRemoveDialog(self)
            choice = dialog.result
            if choice == "location":
                self.remove_text_by_location(obj)
            elif choice == "content":
                self.remove_text_by_content(obj)
        else:
            messagebox.showinfo("Not Supported", f"Removal of '{obj_type}' objects is not yet supported.")
    
    def remove_image_by_xref(self, obj):
        target_xref = obj.get('xref')
        if not target_xref or not messagebox.askyesno("Confirm Image Deletion", f"Remove all instances of Image ID {target_xref} from all pages?"): return
        try:
            images_deleted = 0
            for page in self.doc:
                if page.delete_image(target_xref): images_deleted += 1
            self.status_bar.config(text=f"Deleted {images_deleted} image instance(s). Remember to 'Save As...'")
            messagebox.showinfo("Success", f"{images_deleted} instance(s) marked for deletion. Save the file.")
            self.render_page()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during image deletion: {e}")

    def remove_text_by_location(self, obj):
        target_bbox, target_content = obj.get('bbox'), obj.get('content', '').strip()
        if not target_bbox or not target_content: return
        snippet = (target_content[:30] + '...') if len(target_content) > 30 else target_content
        msg = f"Permanently REMOVE text matching:\n\nContent: \"{snippet}\"\nLocation: Near this area\n\nFrom ALL pages?"
        if not messagebox.askyesno("Confirm Global Text Removal by Location", msg): return
        
        try:
            removed_count = 0
            tolerance = 2.0
            for page in self.doc:
                blocks = page.get_text("blocks")
                for block in blocks:
                    if block[6] == 0 and block[4].strip() == target_content:
                        current_bbox = fitz.Rect(block[:4])
                        if math.isclose(current_bbox.x0, target_bbox.x0, abs_tol=tolerance) and math.isclose(current_bbox.y0, target_bbox.y0, abs_tol=tolerance):
                            page.add_redact_annot(current_bbox)
                            removed_count += 1
            if removed_count == 0:
                messagebox.showinfo("No Matches", "No other matching text blocks were found.")
                return
            for page in self.doc: page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
            self.status_bar.config(text=f"Removed {removed_count} text instance(s). Remember to 'Save As...'")
            messagebox.showinfo("Success", f"{removed_count} instance(s) removed. Save the file.")
            self.render_page()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during text removal: {e}")

    def remove_text_by_content(self, obj):
        target_content = obj.get('content', '').strip()
        if not target_content: return
        snippet = (target_content[:40] + '...') if len(target_content) > 40 else target_content
        msg = f"Permanently REMOVE all occurrences of the text \"{snippet}\" from the ENTIRE PDF, regardless of location?"
        if not messagebox.askyesno("Confirm Global Text Removal by Content", msg): return

        try:
            removed_count = 0
            for page in self.doc:
                areas = page.search_for(target_content)
                for area in areas:
                    page.add_redact_annot(area)
                    removed_count += 1
            if removed_count == 0:
                messagebox.showinfo("No Matches", "That text was not found anywhere else in the document.")
                return
            for page in self.doc: page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
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
        self.resize_timer = self.after(250, self.render_page)

if __name__ == "__main__":
    app = PDFImageRemover()
    app.mainloop()

