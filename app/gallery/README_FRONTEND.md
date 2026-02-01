# Gallery Frontend - Quick Start

## Overview

The frontend is a Multi-Page Application (MPA) using:
- **Django Templates** for server-side rendering
- **HTMX** for interactive updates
- **Tailwind CSS** for styling

## Features Implemented

### ✅ Interactive Features (HTMX)

1. **Toggle Favorite** - Click ⭐/☆ to toggle without page refresh
2. **Add Tags** - Inline form to add tags instantly
3. **Remove Tags** - Click × on any tag to remove it

### ✅ Pages

1. **Gallery List** (`/`) - Browse all galleries with search/filter
2. **Gallery Detail** (`/galleries/<id>/`) - View gallery with albums
3. **Gallery Create/Edit** - Forms for creating/editing galleries
4. **Album Detail** (`/albums/<id>/`) - View album with picture grid
5. **Picture Detail** (`/pictures/<id>/`) - View picture with metadata

## How HTMX Works

### Example: Toggle Favorite

```html
<!-- In template -->
<button hx-post="{% url 'gallery:gallery_toggle_favorite' gallery.id %}"
        hx-target="this"
        hx-swap="outerHTML">
    {% if gallery.is_favorite %}⭐{% else %}☆{% endif %}
</button>
```

**What happens:**
1. User clicks button
2. HTMX sends POST request to `/galleries/<id>/toggle-favorite/`
3. Server returns updated button HTML
4. HTMX replaces the button with new HTML
5. No page refresh!

### Example: Remove Tag

```html
<button hx-delete="{% url 'gallery:gallery_remove_tag' gallery.id %}"
        hx-vals='{"tag": "{{ tag.name }}"}'
        hx-target="closest span"
        hx-swap="outerHTML">
    ×
</button>
```

**What happens:**
1. User clicks × on tag
2. HTMX sends DELETE request with tag name
3. Server removes tag and returns empty string
4. HTMX removes the `<span>` element
5. Tag disappears instantly!

## URL Routes

| URL | View | Description |
|-----|------|-------------|
| `/` | `gallery_list` | List all galleries |
| `/galleries/create/` | `gallery_create` | Create new gallery |
| `/galleries/<id>/` | `gallery_detail` | View gallery |
| `/galleries/<id>/edit/` | `gallery_edit` | Edit gallery |
| `/albums/<id>/` | `album_detail` | View album |
| `/pictures/<id>/` | `picture_detail` | View picture |

## HTMX Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/galleries/<id>/toggle-favorite/` | POST | Toggle favorite |
| `/galleries/<id>/add-tag/` | POST | Add tag |
| `/galleries/<id>/remove-tag/` | DELETE | Remove tag |
| `/albums/<id>/add-tag/` | POST | Add tag |
| `/albums/<id>/remove-tag/` | DELETE | Remove tag |
| `/pictures/<id>/toggle-favorite/` | POST | Toggle favorite |

## Testing

1. **Start the server:**
   ```bash
   python manage.py runserver
   ```

2. **Visit:** `http://localhost:8000/`

3. **Test HTMX:**
   - Click ⭐ to toggle favorite (should update instantly)
   - Add a tag using the inline form
   - Click × on a tag to remove it

## Customization

### Styling
- Edit `static/gallery/css/style.css` for custom styles
- Modify Tailwind classes in templates
- Or replace Tailwind with your CSS framework

### HTMX Behavior
- Modify `hx-target`, `hx-swap` attributes
- Add `hx-trigger` for custom triggers
- Use `hx-indicator` for loading states

## Next Steps

- [ ] Add image upload functionality
- [ ] Implement picture grid with lazy loading
- [ ] Add search with live results (HTMX)
- [ ] Create bulk actions (HTMX)
- [ ] Add drag-and-drop for organizing
