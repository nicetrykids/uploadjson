import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Checkbutton, IntVar, DoubleVar, StringVar
import json
import os
from datetime import datetime
import tkinter.scrolledtext as scrolledtext
import shutil

COMICS_DIR = 'comics'
COMIC_INDEX = os.path.join(COMICS_DIR, 'comic-index.json')

def get_current_datetime():
    """Return current datetime in ISO format."""
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

def ensure_comics_dir():
    if not os.path.exists(COMICS_DIR):
        os.makedirs(COMICS_DIR)

def get_comic_folder(comic_id):
    return os.path.join(COMICS_DIR, str(comic_id))

def get_comic_metadata_path(comic_id):
    return os.path.join(get_comic_folder(comic_id), 'comic.json')

def get_chapter_path(comic_id, vol, chap):
    return os.path.join(get_comic_folder(comic_id), f'chapter_{vol}_{chap}.json')

def load_comics():
    ensure_comics_dir()
    comics = []
    # Use comic-index.json for fast lookup
    index_path = COMIC_INDEX
    if not os.path.exists(index_path):
        return []
    with open(index_path, 'r', encoding='utf-8') as idxf:
        comic_index = json.load(idxf)
    for entry in comic_index:
        comic_id = entry['id']
        folder_path = get_comic_folder(comic_id)
        meta_path = os.path.join(folder_path, 'comic.json')
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                comic = json.load(f)
            # Load chapters using links
            chapters = []
            for chap_link in comic.get('chapters', []):
                chapter_file = os.path.join(folder_path, chap_link['file'])
                if os.path.exists(chapter_file):
                    with open(chapter_file, 'r', encoding='utf-8') as cf:
                        chapters.append(json.load(cf))
            chapters.sort(key=lambda c: (float(c.get('vol', 0)), float(c.get('chap', 0))))
            comic['chapters'] = chapters
            comics.append(comic)
    return comics

def save_comics(comics):
    ensure_comics_dir()
    comic_index = []
    for comic in comics:
        folder = get_comic_folder(comic['id'])
        if not os.path.exists(folder):
            os.makedirs(folder)
        # Save chapters with new naming and collect links
        chapters = comic.get('chapters', [])
        chapter_links = []
        for chap in chapters:
            vol = chap.get('vol', 0)
            chnum = chap.get('chap', 0)
            fname = f"vol_{vol}_chapter_{chnum}.json"
            chapter_path = os.path.join(folder, fname)
            with open(chapter_path, 'w', encoding='utf-8') as cf:
                json.dump(chap, cf, indent=4, ensure_ascii=False)
            chapter_links.append({'vol': vol, 'chap': chnum, 'file': fname})
        # Save metadata (with chapter links)
        meta = dict(comic)
        meta['chapters'] = chapter_links
        with open(get_comic_metadata_path(comic['id']), 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=4, ensure_ascii=False)
        comic_index.append({'id': comic['id'], 'title': comic.get('title', '')})
    # Write comic-index.json
    with open(COMIC_INDEX, 'w', encoding='utf-8') as idxf:
        json.dump(comic_index, idxf, indent=4, ensure_ascii=False)

class TruyenManagermentApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Truyen Managerment')
        self.geometry('1200x700')
        self.comics = load_comics()
        self.tooltip = None
        self.tooltip_id = None
        self.create_widgets()

    def create_widgets(self):
        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(btn_frame, text="Add Comic", command=self.add_comic).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Edit Comic", command=self.edit_comic).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Delete Comic", command=self.delete_comic).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Manage Chapters", command=self.manage_chapters).pack(side=tk.LEFT, padx=2)

        # Treeview
        columns = ("Title", "Type", "Status", "Updated", "Latest Chapter", "Rating", "Star", "Language")
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        self.tree.heading("Title", text="Title")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Updated", text="Last Updated")
        self.tree.heading("Latest Chapter", text="Latest Chapter")
        self.tree.heading("Rating", text="Content Rating")
        self.tree.heading("Star", text="Star Rating")
        self.tree.heading("Language", text="Original Language")
        
        # Column widths
        self.tree.column("Title", width=250)
        self.tree.column("Type", width=80)
        self.tree.column("Status", width=100)
        self.tree.column("Updated", width=150)
        self.tree.column("Latest Chapter", width=150)
        self.tree.column("Rating", width=120)
        self.tree.column("Star", width=80)
        self.tree.column("Language", width=120)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.load_tree()
        
        # Bind tooltip events
        self.tree.bind("<Motion>", self.show_description_tooltip)
        self.tree.bind("<Leave>", self.hide_tooltip)

    def format_date(self, date_str):
        """Format ISO date string to a more readable format."""
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return date_str

    def show_description_tooltip(self, event):
        # Hide the tooltip first
        self.hide_tooltip(None)
        
        # Get the item under mouse
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        # Get index and comic
        idx = self.tree.index(item)
        if idx >= len(self.comics):
            return
            
        comic = self.comics[idx]
        
        # Show description tooltip if available
        if 'description' in comic and comic['description']:
            x, y, width, height = self.tree.bbox(item)
            x = event.x_root
            y = event.y_root + 10
            
            # Create tooltip
            self.tooltip = tk.Toplevel(self)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            # Format description (limit length if too long)
            desc = comic['description']
            if len(desc) > 300:
                desc = desc[:297] + "..."
                
            # Make sure it's not too wide
            desc_lines = []
            for i in range(0, len(desc), 60):
                desc_lines.append(desc[i:i+60])
            desc = "\n".join(desc_lines)
            
            label = tk.Label(self.tooltip, text=desc, justify=tk.LEFT,
                             background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                             font=("Arial", "9", "normal"), padx=5, pady=5)
            label.pack()
            
            # Auto-hide after 5 seconds
            self.tooltip_id = self.after(5000, lambda: self.hide_tooltip(None))

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
        
        if self.tooltip_id:
            self.after_cancel(self.tooltip_id)
            self.tooltip_id = None

    def load_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for comic in self.comics:
            updated_at = comic.get('updated_at', comic.get('createtime', 'N/A'))
            formatted_updated = self.format_date(updated_at)
            
            latest_chapter_at = comic.get('latest_chapter_at', 'N/A')
            formatted_latest = self.format_date(latest_chapter_at)
            
            self.tree.insert('', tk.END, values=(
                comic['title'],
                comic.get('type', 'N/A'),
                comic.get('status', 'N/A'),
                formatted_updated,
                formatted_latest,
                comic.get('content_rating', 'N/A'),
                comic.get('star', 0),
                comic.get('original_language', 'N/A')
            ))

    def add_comic(self):
        dialog = ComicDialog(self, title="Add Comic", is_add=True)
        self.wait_window(dialog)
        if dialog.result:
            new_comic = dialog.result
            new_comic['id'] = self.get_next_id()
            new_comic['chapters'] = []
            current_time = get_current_datetime()
            new_comic['createtime'] = current_time
            new_comic['updated_at'] = current_time
            new_comic['latest_chapter_at'] = 'N/A'
            # Create folder for comic
            ensure_comics_dir()
            os.makedirs(get_comic_folder(new_comic['id']), exist_ok=True)
            self.comics.append(new_comic)
            save_comics(self.comics)
            self.load_tree()

    def edit_comic(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a comic to edit.")
            return
        idx = self.tree.index(selected[0])
        comic = self.comics[idx]
        dialog = ComicDialog(self, title="Edit Comic", comic=comic)
        self.wait_window(dialog)
        if dialog.result:
            for key in dialog.result:
                comic[key] = dialog.result[key]
            comic['updated_at'] = get_current_datetime()
            save_comics(self.comics)
            self.load_tree()

    def delete_comic(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a comic to delete.")
            return
        idx = self.tree.index(selected[0])
        comic = self.comics[idx]
        if messagebox.askyesno("Delete Comic", f"Are you sure you want to delete '{comic['title']}'?"):
            # Remove comic folder
            folder = get_comic_folder(comic['id'])
            if os.path.exists(folder):
                shutil.rmtree(folder)
            del self.comics[idx]
            save_comics(self.comics)
            self.load_tree()

    def get_next_id(self):
        if not self.comics:
            return 1
        return max(c['id'] for c in self.comics) + 1

    def manage_chapters(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a comic to manage chapters.")
            return
        idx = self.tree.index(selected[0])
        comic = self.comics[idx]
        manager = ChapterManager(self, comic, self.save_comic_and_reload)
        manager.comic_index = idx  # Store the comic index for the chapter manager

    def save_comic_and_reload(self, update_timestamp=True, update_latest_chapter=False):
        # Find the comic by its index
        selected = self.tree.selection()
        if selected:
            idx = self.tree.index(selected[0])
            if 0 <= idx < len(self.comics):
                if update_timestamp:
                    self.comics[idx]['updated_at'] = get_current_datetime()
                if update_latest_chapter:
                    self.comics[idx]['latest_chapter_at'] = get_current_datetime()
        
        save_comics(self.comics)
        self.load_tree()

class ComicDialog(tk.Toplevel):
    def __init__(self, parent, title, comic=None, is_add=False):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.comic = comic
        self.is_add = is_add
        self.alt_names = []
        self.arts = []
        self.genres = []
        self.themes = []
        self.formats = []
        self.artists = []
        self.tags = []
        self.demographic_vars = {}
        self.comments = []
        
        if comic:
            if 'alt_names' in comic:
                self.alt_names = [dict(an) for an in comic['alt_names']]
            if 'arts' in comic:
                self.arts = comic['arts']
            if 'genres' in comic:
                self.genres = comic['genres']
            if 'themes' in comic:
                self.themes = comic['themes']
            if 'formats' in comic:
                self.formats = comic['formats']
            if 'artists' in comic:
                self.artists = comic['artists']
            if 'tags' in comic:
                self.tags = comic['tags']
            if 'comments' in comic:
                self.comments = comic['comments']
                
        self.create_widgets()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def create_widgets(self):
        # Create a notebook for tabbed interface
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create frames for different tabs
        basic_frame = ttk.Frame(notebook)
        details_frame = ttk.Frame(notebook)
        metadata_frame = ttk.Frame(notebook)
        
        notebook.add(basic_frame, text="Basic Info")
        notebook.add(details_frame, text="Details")
        notebook.add(metadata_frame, text="Metadata")
        
        # Basic Info Tab
        fields = [
            ("title", "Title"),
            ("author", "Author"),
            ("publication_year", "Publication Year"),
            ("createtime", "Create Time (YYYY-MM-DDTHH:MM:SSZ)"),
            ("mangadex_url", "MangaDex URL"),
            ("pinned", "Pinned (True/False)"),
            ("favorites", "Favorites (True/False)"),
            ("following", "Following (True/False)"),
            ("status", "Status")
        ]
        
        self.entries = {}
        for i, (key, label) in enumerate(fields):
            tk.Label(basic_frame, text=label).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            if key == 'status':
                self.entries[key] = ttk.Combobox(basic_frame, values=["Ongoing", "Completed", "Hiatus", "Cancelled"], state="readonly")
                self.entries[key].grid(row=i, column=1, padx=5, pady=2)
            else:
                entry = tk.Entry(basic_frame)
                entry.grid(row=i, column=1, padx=5, pady=2)
                self.entries[key] = entry
                
        i += 1
        tk.Label(basic_frame, text="Comic Type").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
        self.entries['type'] = ttk.Combobox(basic_frame, values=["Manga", "Manhwa", "Manhua", "Other"], state="readonly")
        self.entries['type'].grid(row=i, column=1, padx=5, pady=2)
        
        i += 1
        tk.Label(basic_frame, text="Original Language").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
        self.entries['original_language'] = tk.Entry(basic_frame)
        self.entries['original_language'].grid(row=i, column=1, padx=5, pady=2)
        
        i += 1
        tk.Label(basic_frame, text="Content Rating").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
        self.entries['content_rating'] = ttk.Combobox(basic_frame, values=["Safe", "Suggestive", "Erotica", "Pornographic"], state="readonly")
        self.entries['content_rating'].grid(row=i, column=1, padx=5, pady=2)
        
        i += 1
        tk.Label(basic_frame, text="Star Rating (0-10)").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
        star_frame = tk.Frame(basic_frame)
        star_frame.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
        self.entries['star'] = tk.Scale(star_frame, from_=0, to=10, orient=tk.HORIZONTAL, resolution=0.1)
        self.entries['star'].pack(side=tk.LEFT)
        
        # Demographics
        i += 1
        tk.Label(basic_frame, text="Demographics").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
        demographics_frame = tk.Frame(basic_frame)
        demographics_frame.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
        demographics = ["Shounen", "Shoujo", "Seinen", "Josei", "None"]
        for j, demo in enumerate(demographics):
            var = tk.BooleanVar()
            self.demographic_vars[demo] = var
            Checkbutton(demographics_frame, text=demo, variable=var).grid(row=0, column=j, padx=2)
            
        # Details Tab - Lists management
        btn_frame = tk.Frame(details_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Alt Names Section
        tk.Button(btn_frame, text="Manage Alternative Names", command=self.manage_alt_names).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Manage Arts", command=self.manage_arts).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Manage Artists", command=self.manage_artists).pack(side=tk.LEFT, padx=2)
        
        lists_frame = tk.Frame(details_frame)
        lists_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left column
        left_frame = tk.Frame(lists_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="Genres").pack(anchor=tk.W)
        self.genres_list = tk.Listbox(left_frame, height=5)
        self.genres_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        genres_btn_frame = tk.Frame(left_frame)
        genres_btn_frame.pack(fill=tk.X)
        tk.Button(genres_btn_frame, text="Add", command=lambda: self.manage_list_item(self.genres, self.genres_list, "Genre")).pack(side=tk.LEFT, padx=2)
        tk.Button(genres_btn_frame, text="Remove", command=lambda: self.remove_list_item(self.genres, self.genres_list)).pack(side=tk.LEFT, padx=2)
        
        # Middle column
        middle_frame = tk.Frame(lists_frame)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(middle_frame, text="Themes").pack(anchor=tk.W)
        self.themes_list = tk.Listbox(middle_frame, height=5)
        self.themes_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        themes_btn_frame = tk.Frame(middle_frame)
        themes_btn_frame.pack(fill=tk.X)
        tk.Button(themes_btn_frame, text="Add", command=lambda: self.manage_list_item(self.themes, self.themes_list, "Theme")).pack(side=tk.LEFT, padx=2)
        tk.Button(themes_btn_frame, text="Remove", command=lambda: self.remove_list_item(self.themes, self.themes_list)).pack(side=tk.LEFT, padx=2)
        
        # Right column
        right_frame = tk.Frame(lists_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_frame, text="Formats").pack(anchor=tk.W)
        self.formats_list = tk.Listbox(right_frame, height=5)
        self.formats_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        formats_btn_frame = tk.Frame(right_frame)
        formats_btn_frame.pack(fill=tk.X)
        tk.Button(formats_btn_frame, text="Add", command=lambda: self.manage_list_item(self.formats, self.formats_list, "Format")).pack(side=tk.LEFT, padx=2)
        tk.Button(formats_btn_frame, text="Remove", command=lambda: self.remove_list_item(self.formats, self.formats_list)).pack(side=tk.LEFT, padx=2)
        
        # Tags frame
        tags_frame = tk.Frame(details_frame)
        tags_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(tags_frame, text="Tags").pack(anchor=tk.W)
        self.tags_list = tk.Listbox(tags_frame, height=5)
        self.tags_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        tags_btn_frame = tk.Frame(tags_frame)
        tags_btn_frame.pack(fill=tk.X)
        tk.Button(tags_btn_frame, text="Add", command=lambda: self.manage_list_item(self.tags, self.tags_list, "Tag")).pack(side=tk.LEFT, padx=2)
        tk.Button(tags_btn_frame, text="Remove", command=lambda: self.remove_list_item(self.tags, self.tags_list)).pack(side=tk.LEFT, padx=2)
        
        # Metadata Tab - Comments
        tk.Label(metadata_frame, text="Description").pack(anchor=tk.W, padx=5, pady=2)
        self.description_text = scrolledtext.ScrolledText(metadata_frame, height=6)
        self.description_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        tk.Label(metadata_frame, text="Comments").pack(anchor=tk.W, padx=5, pady=2)
        self.comments_text = scrolledtext.ScrolledText(metadata_frame, height=10)
        self.comments_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Load the list data if editing
        self.load_list_data()
        
        # Bottom buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(btn_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)
        
        # Init values if editing
        if self.comic:
            for key, entry in self.entries.items():
                if key in ['status', 'type', 'content_rating']:
                    if key in self.comic:
                        entry.set(self.comic[key])
                elif key == 'star':
                    entry.set(self.comic.get(key, 0))
                else:
                    entry.delete(0, tk.END)
                    if key in self.comic:
                        entry.insert(0, str(self.comic[key]))
            
            # Set demographics checkboxes
            if 'demographics' in self.comic:
                for demo in self.comic['demographics']:
                    if demo in self.demographic_vars:
                        self.demographic_vars[demo].set(True)
            
            # Set description
            if 'description' in self.comic:
                self.description_text.insert(tk.END, self.comic['description'])
            
            # Set comments
            if 'comments' in self.comic:
                comments_str = "\n".join(f"{c['author']}: {c['text']} [{c['date']}]" for c in self.comic['comments'])
                self.comments_text.insert(tk.END, comments_str)
        
        elif self.is_add:
            now = get_current_datetime()
            self.entries['createtime'].insert(0, now)
            self.entries['pinned'].insert(0, 'False')
            self.entries['favorites'].insert(0, 'False')
            self.entries['following'].insert(0, 'False')
            self.entries['status'].set('Ongoing')
            self.entries['type'].set('Manga')
            self.entries['content_rating'].set('Safe')
            self.entries['star'].set(0)
            current_year = datetime.now().year
            self.entries['publication_year'].insert(0, str(current_year))

    def load_list_data(self):
        # Clear and reload all listboxes
        self.genres_list.delete(0, tk.END)
        self.themes_list.delete(0, tk.END)
        self.formats_list.delete(0, tk.END)
        self.tags_list.delete(0, tk.END)
        
        for genre in self.genres:
            self.genres_list.insert(tk.END, genre)
        
        for theme in self.themes:
            self.themes_list.insert(tk.END, theme)
            
        for format in self.formats:
            self.formats_list.insert(tk.END, format)
            
        for tag in self.tags:
            self.tags_list.insert(tk.END, tag)

    def manage_list_item(self, item_list, listbox, item_type):
        new_item = simpledialog.askstring(f"Add {item_type}", f"Enter {item_type}:")
        if new_item and new_item not in item_list:
            item_list.append(new_item)
            listbox.insert(tk.END, new_item)

    def remove_list_item(self, item_list, listbox):
        selected = listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        del item_list[idx]
        listbox.delete(idx)

    def manage_alt_names(self):
        dialog = AltNamesDialog(self, self.alt_names)
        self.wait_window(dialog)
        if dialog.result is not None:
            self.alt_names = dialog.result

    def manage_arts(self):
        dialog = ListDialog(self, "Manage Arts", self.arts, "Art URL")
        self.wait_window(dialog)
        if dialog.result is not None:
            self.arts = dialog.result
            
    def manage_artists(self):
        dialog = ListDialog(self, "Manage Artists", self.artists, "Artist Name")
        self.wait_window(dialog)
        if dialog.result is not None:
            self.artists = dialog.result

    def on_ok(self):
        try:
            # Parse comments from text field
            comments_text = self.comments_text.get('1.0', tk.END).strip()
            comments = []
            if comments_text:
                lines = comments_text.splitlines()
                for line in lines:
                    if ':' in line and '[' in line and ']' in line:
                        author, rest = line.split(':', 1)
                        text_part, date_part = rest.rsplit('[', 1)
                        date = date_part.rstrip(']').strip()
                        text = text_part.strip()
                        comments.append({
                            'author': author.strip(),
                            'text': text,
                            'date': date
                        })
            
            # Get selected demographics
            demographics = [demo for demo, var in self.demographic_vars.items() if var.get()]
            
            result = {
                'title': self.entries['title'].get(),
                'author': self.entries['author'].get(),
                'publication_year': int(self.entries['publication_year'].get()) if self.entries['publication_year'].get() else None,
                'createtime': self.entries['createtime'].get(),
                'mangadex_url': self.entries['mangadex_url'].get(),
                'pinned': self.entries['pinned'].get().lower() == 'true',
                'favorites': self.entries['favorites'].get().lower() == 'true',
                'following': self.entries['following'].get().lower() == 'true',
                'status': self.entries['status'].get(),
                'type': self.entries['type'].get(),
                'original_language': self.entries['original_language'].get(),
                'content_rating': self.entries['content_rating'].get(),
                'star': float(self.entries['star'].get()),
                'demographics': demographics,
                'description': self.description_text.get('1.0', tk.END).strip(),
                'alt_names': self.alt_names,
                'arts': self.arts,
                'genres': self.genres,
                'themes': self.themes,
                'formats': self.formats,
                'artists': self.artists,
                'tags': self.tags,
                'comments': comments
            }
            self.result = result
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

class AltNamesDialog(tk.Toplevel):
    def __init__(self, parent, alt_names):
        super().__init__(parent)
        self.title("Manage Alternative Names")
        self.result = None
        self.alt_names = [dict(an) for an in alt_names]
        self.create_widgets()
        self.load_alt_names()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def create_widgets(self):
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(btn_frame, text="Add", command=self.add_alt_name).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Edit", command=self.edit_alt_name).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Delete", command=self.delete_alt_name).pack(side=tk.LEFT, padx=2)
        self.tree = ttk.Treeview(self, columns=("Language", "Name"), show='headings')
        self.tree.heading("Language", text="Language")
        self.tree.heading("Name", text="Name")
        self.tree.pack(fill=tk.BOTH, expand=True)
        tk.Button(self, text="OK", command=self.on_ok).pack(pady=10)

    def load_alt_names(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for an in self.alt_names:
            self.tree.insert('', tk.END, values=(an.get('language', ''), an.get('name', '')))

    def add_alt_name(self):
        dialog = AltNameEditDialog(self, title="Add Alternative Name")
        self.wait_window(dialog)
        if dialog.result:
            self.alt_names.append(dialog.result)
            self.load_alt_names()

    def edit_alt_name(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select an alternative name to edit.")
            return
        idx = self.tree.index(selected[0])
        alt_name = self.alt_names[idx]
        dialog = AltNameEditDialog(self, title="Edit Alternative Name", alt_name=alt_name)
        self.wait_window(dialog)
        if dialog.result:
            self.alt_names[idx] = dialog.result
            self.load_alt_names()

    def delete_alt_name(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select an alternative name to delete.")
            return
        idx = self.tree.index(selected[0])
        del self.alt_names[idx]
        self.load_alt_names()

    def on_ok(self):
        self.result = self.alt_names
        self.destroy()

class AltNameEditDialog(tk.Toplevel):
    def __init__(self, parent, title, alt_name=None):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.alt_name = alt_name
        self.create_widgets()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def create_widgets(self):
        tk.Label(self, text="Language").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.language_entry = tk.Entry(self)
        self.language_entry.grid(row=0, column=1, padx=5, pady=2)
        tk.Label(self, text="Name").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.name_entry = tk.Entry(self)
        self.name_entry.grid(row=1, column=1, padx=5, pady=2)
        if self.alt_name:
            self.language_entry.insert(0, self.alt_name.get('language', ''))
            self.name_entry.insert(0, self.alt_name.get('name', ''))
        tk.Button(self, text="OK", command=self.on_ok).grid(row=2, column=0, pady=10)
        tk.Button(self, text="Cancel", command=self.destroy).grid(row=2, column=1, pady=10)

    def on_ok(self):
        self.result = {
            'language': self.language_entry.get(),
            'name': self.name_entry.get()
        }
        self.destroy()

class ListDialog(tk.Toplevel):
    def __init__(self, parent, title, items, item_label):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.items = list(items)  # Create a copy of the list
        self.item_label = item_label
        self.create_widgets()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def create_widgets(self):
        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(btn_frame, text="Add", command=self.add_item).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Edit", command=self.edit_item).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Delete", command=self.delete_item).pack(side=tk.LEFT, padx=2)
        
        # List
        self.listbox = tk.Listbox(self, width=50, height=10)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Load items
        for item in self.items:
            self.listbox.insert(tk.END, item)
            
        # OK/Cancel buttons
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(bottom_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def add_item(self):
        new_item = simpledialog.askstring(f"Add {self.item_label}", f"Enter {self.item_label}:")
        if new_item:
            self.items.append(new_item)
            self.listbox.insert(tk.END, new_item)

    def edit_item(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showwarning("No selection", f"Please select an {self.item_label.lower()} to edit.")
            return
        idx = selected[0]
        current = self.items[idx]
        new_item = simpledialog.askstring(f"Edit {self.item_label}", f"Edit {self.item_label}:", initialvalue=current)
        if new_item:
            self.items[idx] = new_item
            self.listbox.delete(idx)
            self.listbox.insert(idx, new_item)

    def delete_item(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showwarning("No selection", f"Please select an {self.item_label.lower()} to delete.")
            return
        idx = selected[0]
        del self.items[idx]
        self.listbox.delete(idx)

    def on_ok(self):
        self.result = self.items
        self.destroy()

class ChapterManager(tk.Toplevel):
    def __init__(self, parent, comic, on_save):
        super().__init__(parent)
        self.title(f"Manage Chapters - {comic['title']}")
        self.comic = comic
        self.on_save = on_save
        self.comic_index = -1  # Will be set by the parent
        self.create_widgets()
        self.load_chapters()
        self.grab_set()

    def create_widgets(self):
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(btn_frame, text="Add Chapter", command=self.add_chapter).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Edit Chapter", command=self.edit_chapter).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Delete Chapter", command=self.delete_chapter).pack(side=tk.LEFT, padx=2)

        columns = ("Vol", "Chap", "Language", "Updated", "Reading Progress", "Comments", "Images")
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        self.tree.heading("Vol", text="Vol")
        self.tree.heading("Chap", text="Chap")
        self.tree.heading("Language", text="Language")
        self.tree.heading("Updated", text="Last Updated")
        self.tree.heading("Reading Progress", text="Reading Progress")
        self.tree.heading("Comments", text="Comments")
        self.tree.heading("Images", text="Images")
        
        # Column widths
        self.tree.column("Vol", width=50)
        self.tree.column("Chap", width=50)
        self.tree.column("Language", width=80)
        self.tree.column("Updated", width=150)
        self.tree.column("Reading Progress", width=120)
        self.tree.column("Comments", width=120)
        self.tree.column("Images", width=200)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def format_date(self, date_str):
        """Format ISO date string to a more readable format."""
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return date_str
    
    def load_chapters(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for chap in self.comic.get('chapters', []):
            comment_count = len(chap.get('comments', []))
            comment_text = f"{comment_count} comment(s)" if comment_count > 0 else "No comments"
            
            # Get and format the updated_at date
            updated_at = chap.get('updated_at', 'N/A')
            formatted_date = self.format_date(updated_at)
            
            self.tree.insert('', tk.END, values=(
                chap['vol'], 
                chap['chap'], 
                chap.get('language', ''), 
                formatted_date,
                chap['reading_progress'],
                comment_text,
                f"{len(chap['images'])} image(s)"
            ))

    def add_chapter(self):
        dialog = ChapterDialog(self, title="Add Chapter")
        self.wait_window(dialog)
        if dialog.result:
            chapter = dialog.result
            current_time = get_current_datetime()
            chapter['created_at'] = current_time
            chapter['updated_at'] = current_time
            self.comic.setdefault('chapters', []).append(chapter)
            # Save chapter as file with new naming
            folder = get_comic_folder(self.comic['id'])
            vol = chapter.get('vol', 0)
            chnum = chapter.get('chap', 0)
            chapter_path = os.path.join(folder, f"vol_{vol}_chapter_{chnum}.json")
            with open(chapter_path, 'w', encoding='utf-8') as cf:
                json.dump(chapter, cf, indent=4, ensure_ascii=False)
            self.on_save(update_timestamp=True, update_latest_chapter=True)
            self.load_chapters()

    def edit_chapter(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a chapter to edit.")
            return
        idx = self.tree.index(selected[0])
        chapter = self.comic['chapters'][idx]
        dialog = ChapterDialog(self, title="Edit Chapter", chapter=chapter)
        self.wait_window(dialog)
        if dialog.result:
            updated_chapter = dialog.result
            updated_chapter['updated_at'] = get_current_datetime()
            if 'created_at' in chapter:
                updated_chapter['created_at'] = chapter['created_at']
            self.comic['chapters'][idx] = updated_chapter
            # Save updated chapter as file with new naming
            folder = get_comic_folder(self.comic['id'])
            vol = updated_chapter.get('vol', 0)
            chnum = updated_chapter.get('chap', 0)
            chapter_path = os.path.join(folder, f"vol_{vol}_chapter_{chnum}.json")
            with open(chapter_path, 'w', encoding='utf-8') as cf:
                json.dump(updated_chapter, cf, indent=4, ensure_ascii=False)
            self.on_save(update_timestamp=True, update_latest_chapter=False)
            self.load_chapters()

    def delete_chapter(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a chapter to delete.")
            return
        idx = self.tree.index(selected[0])
        chapter = self.comic['chapters'][idx]
        if messagebox.askyesno("Delete Chapter", "Are you sure you want to delete this chapter?"):
            # Remove chapter file with new naming
            folder = get_comic_folder(self.comic['id'])
            vol = chapter.get('vol', 0)
            chnum = chapter.get('chap', 0)
            chapter_path = os.path.join(folder, f"vol_{vol}_chapter_{chnum}.json")
            if os.path.exists(chapter_path):
                os.remove(chapter_path)
            del self.comic['chapters'][idx]
            self.on_save(update_timestamp=True, update_latest_chapter=False)
            self.load_chapters()

class ChapterDialog(tk.Toplevel):
    def __init__(self, parent, title, chapter=None):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.chapter = chapter
        self.comments = []
        if chapter and 'comments' in chapter:
            self.comments = chapter['comments']
        self.create_widgets()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create frames for tabs
        basic_frame = ttk.Frame(notebook)
        comments_frame = ttk.Frame(notebook)
        
        notebook.add(basic_frame, text="Basic Info")
        notebook.add(comments_frame, text="Comments")
        
        # Basic fields
        fields = [
            ("chapter_name", "Chapter Name"),
            ("vol", "Volume"),
            ("chap", "Chapter"),
            ("language", "Language (e.g. en, jp, vi)"),
            ("reading_progress", "Reading Progress (Image Index)"),
            ("images", "Images (one URL per line)")
        ]
        self.entries = {}
        for i, (key, label) in enumerate(fields):
            tk.Label(basic_frame, text=label).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            if key == 'images':
                text = tk.Text(basic_frame, height=5, width=40)
                text.grid(row=i, column=1, padx=5, pady=2)
                self.entries[key] = text
            else:
                entry = tk.Entry(basic_frame)
                entry.grid(row=i, column=1, padx=5, pady=2)
                self.entries[key] = entry
        # One Shot checkbox
        self.one_shot_var = tk.BooleanVar()
        tk.Checkbutton(basic_frame, text="One Shot", variable=self.one_shot_var).grid(row=len(fields), column=1, sticky=tk.W, padx=5, pady=2)
        
        # Comments tab
        tk.Label(comments_frame, text="Comments").pack(anchor=tk.W, padx=5, pady=2)
        self.comments_text = scrolledtext.ScrolledText(comments_frame, height=10, width=40)
        self.comments_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        if self.chapter:
            self.entries['chapter_name'].insert(0, self.chapter.get('chapter_name', ''))
            self.entries['vol'].insert(0, str(self.chapter.get('vol', '')))
            self.entries['chap'].insert(0, str(self.chapter.get('chap', '')))
            self.entries['language'].insert(0, self.chapter.get('language', ''))
            self.entries['reading_progress'].insert(0, str(self.chapter.get('reading_progress', 0)))
            self.entries['images'].insert('1.0', '\n'.join(self.chapter.get('images', [])))
            self.one_shot_var.set(self.chapter.get('one_shot', False))
            # Set comments
            if 'comments' in self.chapter:
                comments_str = "\n".join(f"{c['author']}: {c['text']} [{c['date']}]" for c in self.chapter['comments'])
                self.comments_text.insert(tk.END, comments_str)
        else:
            self.entries['reading_progress'].insert(0, '0')
            self.one_shot_var.set(False)
        
        # Bottom buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(btn_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def on_ok(self):
        try:
            images_text = self.entries['images'].get('1.0', tk.END)
            images = [line.strip() for line in images_text.splitlines() if line.strip()]
            # Parse comments from text field
            comments_text = self.comments_text.get('1.0', tk.END).strip()
            comments = []
            if comments_text:
                lines = comments_text.splitlines()
                for line in lines:
                    if ':' in line and '[' in line and ']' in line:
                        author, rest = line.split(':', 1)
                        text_part, date_part = rest.rsplit('[', 1)
                        date = date_part.rstrip(']').strip()
                        text = text_part.strip()
                        comments.append({
                            'author': author.strip(),
                            'text': text,
                            'date': date
                        })
            result = {
                'chapter_name': self.entries['chapter_name'].get(),
                'vol': int(self.entries['vol'].get()),
                'chap': int(self.entries['chap'].get()),
                'language': self.entries['language'].get(),
                'reading_progress': int(self.entries['reading_progress'].get()),
                'images': images,
                'comments': comments,
                'one_shot': self.one_shot_var.get()
            }
            self.result = result
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == '__main__':
    app = TruyenManagermentApp()
    app.mainloop()
