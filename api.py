import json
from TruyenManagerment import (
    load_comics, save_comics, get_current_datetime, ensure_comics_dir,
    get_comic_folder, get_comic_metadata_path, get_chapter_path
)
import os

class ComicAPI:
    def get_comics(self):
        """Lấy danh sách tất cả comics, kèm chapters, alt_names, ..."""
        comics = load_comics()
        return json.dumps({"success": True, "data": comics})

    def get_comic(self, comic_id):
        """Lấy chi tiết một comic theo id."""
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                return json.dumps({"success": True, "data": comic})
        return json.dumps({"success": False, "error": "Comic not found"})

    def add_comic(self, comic_data):
        """Thêm một comic mới. comic_data là dict (từ JSON)."""
        comics = load_comics()
        new_id = max([c['id'] for c in comics], default=0) + 1
        comic_data['id'] = new_id
        comic_data['chapters'] = []
        now = get_current_datetime()
        comic_data['createtime'] = now
        comic_data['updated_at'] = now
        comic_data['latest_chapter_at'] = 'N/A'
        ensure_comics_dir()
        os.makedirs(get_comic_folder(new_id), exist_ok=True)
        # Convert 'chap' in chapters to float if present
        if 'chapters' in comic_data:
            for chapter in comic_data['chapters']:
                if 'chap' in chapter:
                    try:
                        chapter['chap'] = float(chapter['chap'])
                    except Exception:
                        chapter['chap'] = 0.0
        comics.append(comic_data)
        save_comics(comics)
        return json.dumps({"success": True, "data": comic_data})

    def edit_comic(self, comic_id, comic_data):
        """Sửa thông tin một comic."""
        comics = load_comics()
        for i, comic in enumerate(comics):
            if str(comic['id']) == str(comic_id):
                # Nếu có chapters, đảm bảo mọi chapter['chap'] là float
                if 'chapters' in comic_data:
                    for chapter in comic_data['chapters']:
                        if 'chap' in chapter:
                            try:
                                chapter['chap'] = float(chapter['chap'])
                            except Exception:
                                chapter['chap'] = 0.0
                # Nếu không có chapters trong comic_data nhưng có trong comic, vẫn đảm bảo mọi chapter['chap'] là float
                elif 'chapters' in comic:
                    for chapter in comic['chapters']:
                        if 'chap' in chapter:
                            try:
                                chapter['chap'] = float(chapter['chap'])
                            except Exception:
                                chapter['chap'] = 0.0
                for key in comic_data:
                    comic[key] = comic_data[key]
                comic['updated_at'] = get_current_datetime()
                comics[i] = comic
                save_comics(comics)
                return json.dumps({"success": True, "data": comic})
        return json.dumps({"success": False, "error": "Comic not found"})

    def delete_comic(self, comic_id):
        """Xóa một comic."""
        comics = load_comics()
        for i, comic in enumerate(comics):
            if str(comic['id']) == str(comic_id):
                folder = get_comic_folder(comic['id'])
                if os.path.exists(folder):
                    import shutil
                    shutil.rmtree(folder)
                del comics[i]
                save_comics(comics)
                return json.dumps({"success": True})
        return json.dumps({"success": False, "error": "Comic not found"})

    def add_chapter(self, comic_id, chapter_data):
        """Thêm chapter cho comic."""
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                now = get_current_datetime()
                chapter_data['created_at'] = now
                chapter_data['updated_at'] = now
                comic.setdefault('chapters', []).append(chapter_data)
                # Lưu file chapter
                folder = get_comic_folder(comic['id'])
                vol = chapter_data.get('vol', 0)
                chnum = chapter_data.get('chap', 0)
                chapter_path = os.path.join(folder, f"vol_{vol}_chapter_{chnum}.json")
                with open(chapter_path, 'w', encoding='utf-8') as cf:
                    json.dump(chapter_data, cf, indent=4, ensure_ascii=False)
                save_comics(comics)
                return json.dumps({"success": True, "data": chapter_data})
        return json.dumps({"success": False, "error": "Comic not found"})

    def edit_chapter(self, comic_id, vol, chap, chapter_data):
        """Sửa chapter cho comic."""
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                for i, c in enumerate(comic.get('chapters', [])):
                    if c.get('vol') == vol and c.get('chap') == chap:
                        chapter_data['updated_at'] = get_current_datetime()
                        if 'created_at' in c:
                            chapter_data['created_at'] = c['created_at']
                        comic['chapters'][i] = chapter_data
                        # Lưu file chapter
                        folder = get_comic_folder(comic['id'])
                        chapter_path = os.path.join(folder, f"vol_{vol}_chapter_{chap}.json")
                        with open(chapter_path, 'w', encoding='utf-8') as cf:
                            json.dump(chapter_data, cf, indent=4, ensure_ascii=False)
                        save_comics(comics)
                        return json.dumps({"success": True, "data": chapter_data})
                return json.dumps({"success": False, "error": "Chapter not found"})
        return json.dumps({"success": False, "error": "Comic not found"})

    def delete_chapter(self, comic_id, vol, chap):
        """Xóa chapter cho comic."""
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                for i, c in enumerate(comic.get('chapters', [])):
                    if c.get('vol') == vol and c.get('chap') == chap:
                        # Xóa file chapter
                        folder = get_comic_folder(comic['id'])
                        chapter_path = os.path.join(folder, f"vol_{vol}_chapter_{chap}.json")
                        if os.path.exists(chapter_path):
                            os.remove(chapter_path)
                        del comic['chapters'][i]
                        save_comics(comics)
                        return json.dumps({"success": True})
                return json.dumps({"success": False, "error": "Chapter not found"})
        return json.dumps({"success": False, "error": "Comic not found"})

    # --- ALT NAMES ---
    def get_alt_names(self, comic_id):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                return json.dumps({"success": True, "data": comic.get('alt_names', [])})
        return json.dumps({"success": False, "error": "Comic not found"})

    def add_alt_name(self, comic_id, alt_name):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                comic.setdefault('alt_names', []).append(alt_name)
                comic['updated_at'] = get_current_datetime()
                save_comics(comics)
                return json.dumps({"success": True, "data": comic['alt_names']})
        return json.dumps({"success": False, "error": "Comic not found"})

    def edit_alt_name(self, comic_id, index, alt_name):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('alt_names', [])):
                    comic['alt_names'][index] = alt_name
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['alt_names']})
                return json.dumps({"success": False, "error": "Alt name index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    def delete_alt_name(self, comic_id, index):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('alt_names', [])):
                    del comic['alt_names'][index]
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['alt_names']})
                return json.dumps({"success": False, "error": "Alt name index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    # --- GENRES ---
    def get_genres(self, comic_id):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                return json.dumps({"success": True, "data": comic.get('genres', [])})
        return json.dumps({"success": False, "error": "Comic not found"})

    def add_genre(self, comic_id, genre):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                comic.setdefault('genres', []).append(genre)
                comic['updated_at'] = get_current_datetime()
                save_comics(comics)
                return json.dumps({"success": True, "data": comic['genres']})
        return json.dumps({"success": False, "error": "Comic not found"})

    def edit_genre(self, comic_id, index, genre):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('genres', [])):
                    comic['genres'][index] = genre
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['genres']})
                return json.dumps({"success": False, "error": "Genre index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    def delete_genre(self, comic_id, index):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('genres', [])):
                    del comic['genres'][index]
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['genres']})
                return json.dumps({"success": False, "error": "Genre index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    # --- THEMES ---
    def get_themes(self, comic_id):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                return json.dumps({"success": True, "data": comic.get('themes', [])})
        return json.dumps({"success": False, "error": "Comic not found"})

    def add_theme(self, comic_id, theme):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                comic.setdefault('themes', []).append(theme)
                comic['updated_at'] = get_current_datetime()
                save_comics(comics)
                return json.dumps({"success": True, "data": comic['themes']})
        return json.dumps({"success": False, "error": "Comic not found"})

    def edit_theme(self, comic_id, index, theme):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('themes', [])):
                    comic['themes'][index] = theme
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['themes']})
                return json.dumps({"success": False, "error": "Theme index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    def delete_theme(self, comic_id, index):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('themes', [])):
                    del comic['themes'][index]
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['themes']})
                return json.dumps({"success": False, "error": "Theme index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    # --- FORMATS ---
    def get_formats(self, comic_id):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                return json.dumps({"success": True, "data": comic.get('formats', [])})
        return json.dumps({"success": False, "error": "Comic not found"})

    def add_format(self, comic_id, format_):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                comic.setdefault('formats', []).append(format_)
                comic['updated_at'] = get_current_datetime()
                save_comics(comics)
                return json.dumps({"success": True, "data": comic['formats']})
        return json.dumps({"success": False, "error": "Comic not found"})

    def edit_format(self, comic_id, index, format_):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('formats', [])):
                    comic['formats'][index] = format_
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['formats']})
                return json.dumps({"success": False, "error": "Format index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    def delete_format(self, comic_id, index):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('formats', [])):
                    del comic['formats'][index]
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['formats']})
                return json.dumps({"success": False, "error": "Format index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    # --- TAGS ---
    def get_tags(self, comic_id):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                return json.dumps({"success": True, "data": comic.get('tags', [])})
        return json.dumps({"success": False, "error": "Comic not found"})

    def add_tag(self, comic_id, tag):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                comic.setdefault('tags', []).append(tag)
                comic['updated_at'] = get_current_datetime()
                save_comics(comics)
                return json.dumps({"success": True, "data": comic['tags']})
        return json.dumps({"success": False, "error": "Comic not found"})

    def edit_tag(self, comic_id, index, tag):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('tags', [])):
                    comic['tags'][index] = tag
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['tags']})
                return json.dumps({"success": False, "error": "Tag index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    def delete_tag(self, comic_id, index):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('tags', [])):
                    del comic['tags'][index]
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['tags']})
                return json.dumps({"success": False, "error": "Tag index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    # --- ARTISTS ---
    def get_artists(self, comic_id):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                return json.dumps({"success": True, "data": comic.get('artists', [])})
        return json.dumps({"success": False, "error": "Comic not found"})

    def add_artist(self, comic_id, artist):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                comic.setdefault('artists', []).append(artist)
                comic['updated_at'] = get_current_datetime()
                save_comics(comics)
                return json.dumps({"success": True, "data": comic['artists']})
        return json.dumps({"success": False, "error": "Comic not found"})

    def edit_artist(self, comic_id, index, artist):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('artists', [])):
                    comic['artists'][index] = artist
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['artists']})
                return json.dumps({"success": False, "error": "Artist index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    def delete_artist(self, comic_id, index):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('artists', [])):
                    del comic['artists'][index]
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['artists']})
                return json.dumps({"success": False, "error": "Artist index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    # --- ARTS ---
    def get_arts(self, comic_id):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                return json.dumps({"success": True, "data": comic.get('arts', [])})
        return json.dumps({"success": False, "error": "Comic not found"})

    def add_art(self, comic_id, art):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                comic.setdefault('arts', []).append(art)
                comic['updated_at'] = get_current_datetime()
                save_comics(comics)
                return json.dumps({"success": True, "data": comic['arts']})
        return json.dumps({"success": False, "error": "Comic not found"})

    def edit_art(self, comic_id, index, art):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('arts', [])):
                    comic['arts'][index] = art
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['arts']})
                return json.dumps({"success": False, "error": "Art index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    def delete_art(self, comic_id, index):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('arts', [])):
                    del comic['arts'][index]
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['arts']})
                return json.dumps({"success": False, "error": "Art index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    # --- COMMENTS (comic-level) ---
    def get_comments(self, comic_id):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                return json.dumps({"success": True, "data": comic.get('comments', [])})
        return json.dumps({"success": False, "error": "Comic not found"})

    def add_comment(self, comic_id, comment):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                comic.setdefault('comments', []).append(comment)
                comic['updated_at'] = get_current_datetime()
                save_comics(comics)
                return json.dumps({"success": True, "data": comic['comments']})
        return json.dumps({"success": False, "error": "Comic not found"})

    def edit_comment(self, comic_id, index, comment):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('comments', [])):
                    comic['comments'][index] = comment
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['comments']})
                return json.dumps({"success": False, "error": "Comment index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    def delete_comment(self, comic_id, index):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                if 0 <= index < len(comic.get('comments', [])):
                    del comic['comments'][index]
                    comic['updated_at'] = get_current_datetime()
                    save_comics(comics)
                    return json.dumps({"success": True, "data": comic['comments']})
                return json.dumps({"success": False, "error": "Comment index out of range"})
        return json.dumps({"success": False, "error": "Comic not found"})

    # --- DEMOGRAPHICS ---
    def get_demographics(self, comic_id):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                return json.dumps({"success": True, "data": comic.get('demographics', [])})
        return json.dumps({"success": False, "error": "Comic not found"})

    def set_demographics(self, comic_id, demographics):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                comic['demographics'] = demographics
                comic['updated_at'] = get_current_datetime()
                save_comics(comics)
                return json.dumps({"success": True, "data": comic['demographics']})
        return json.dumps({"success": False, "error": "Comic not found"})

    # --- STAR ---
    def get_star(self, comic_id):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                return json.dumps({"success": True, "data": comic.get('star', 0)})
        return json.dumps({"success": False, "error": "Comic not found"})

    def set_star(self, comic_id, star):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                comic['star'] = star
                comic['updated_at'] = get_current_datetime()
                save_comics(comics)
                return json.dumps({"success": True, "data": comic['star']})
        return json.dumps({"success": False, "error": "Comic not found"})

    # --- DESCRIPTION ---
    def get_description(self, comic_id):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                return json.dumps({"success": True, "data": comic.get('description', '')})
        return json.dumps({"success": False, "error": "Comic not found"})

    def set_description(self, comic_id, description):
        comics = load_comics()
        for comic in comics:
            if str(comic['id']) == str(comic_id):
                comic['description'] = description
                comic['updated_at'] = get_current_datetime()
                save_comics(comics)
                return json.dumps({"success": True, "data": comic['description']})
        return json.dumps({"success": False, "error": "Comic not found"})

    # --- ALL DATA ---
    def get_all_genres(self):
        comics = load_comics()
        genres = set()
        for comic in comics:
            for g in comic.get('genres', []):
                genres.add(g)
        return json.dumps({"success": True, "data": sorted(genres)})

    def get_all_themes(self):
        comics = load_comics()
        themes = set()
        for comic in comics:
            for t in comic.get('themes', []):
                themes.add(t)
        return json.dumps({"success": True, "data": sorted(themes)})

    def get_all_formats(self):
        comics = load_comics()
        formats = set()
        for comic in comics:
            for f in comic.get('formats', []):
                formats.add(f)
        return json.dumps({"success": True, "data": sorted(formats)})

    def get_all_tags(self):
        comics = load_comics()
        tags = set()
        for comic in comics:
            for t in comic.get('tags', []):
                tags.add(t)
        return json.dumps({"success": True, "data": sorted(tags)})

    def get_all_artists(self):
        comics = load_comics()
        artists = set()
        for comic in comics:
            for a in comic.get('artists', []):
                artists.add(a)
        return json.dumps({"success": True, "data": sorted(artists)})
