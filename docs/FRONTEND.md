# Frontend Documentation - Gallery App

## Overview

The Gallery app uses a **Multi-Page Application (MPA)** approach with Django templates and HTMX for interactive updates.

## Architecture

- **Django Templates**: Server-rendered HTML pages
- **HTMX**: For interactive updates without full page refresh
- **Tailwind CSS**: For styling (via CDN)
- **No JavaScript Framework**: Pure Django + HTMX

## Features

### HTMX-Powered Interactions

1. **Toggle Favorite** (⭐/☆)
   - Galleries and Pictures
   - Updates instantly without page refresh
   - Uses `hx-post` to toggle favorite status

2. **Add/Remove Tags**
   - Interactive tag management
   - Add tags via inline form
   - Remove tags with × button
   - Updates in real-time

3. **Search and Filter**
   - Server-side filtering
   - Full page navigation (traditional MPA)

## Template Structure

```
gallery/templates/gallery/
├── base.html              # Base template with navigation
├── gallery_list.html      # List of galleries
├── gallery_detail.html    # Gallery details with albums
├── gallery_form.html      # Create/Edit gallery form
├── album_detail.html      # Album with pictures grid
├── album_form.html        # Create/Edit album form
├── picture_detail.html    # Picture view with metadata
└── partials/
    ├── favorite_button.html  # HTMX favorite toggle button
    └── tags_list.html        # HTMX tags list with add/remove
```

## HTMX Endpoints

### Gallery Endpoints

- `POST /galleries/<id>/toggle-favorite/` - Toggle favorite status
- `POST /galleries/<id>/add-tag/` - Add tag to gallery
- `DELETE /galleries/<id>/remove-tag/` - Remove tag from gallery

### Album Endpoints

- `POST /albums/<id>/add-tag/` - Add tag to album
- `DELETE /albums/<id>/remove-tag/` - Remove tag from album

### Picture Endpoints

- `POST /pictures/<id>/toggle-favorite/` - Toggle favorite status

## HTMX Usage Examples

### Toggle Favorite

```html
<button hx-post="{% url 'gallery:gallery_toggle_favorite' gallery.id %}"
        hx-target="this"
        hx-swap="outerHTML">
    {% if gallery.is_favorite %}⭐{% else %}☆{% endif %}
</button>
```

### Remove Tag

```html
<button hx-delete="{% url 'gallery:gallery_remove_tag' gallery.id %}"
        hx-vals='{"tag": "{{ tag.name }}"}'
        hx-target="closest span"
        hx-swap="outerHTML">
    ×
</button>
```

### Add Tag

```html
<form hx-post="{% url 'gallery:gallery_add_tag' gallery.id %}"
      hx-target="closest div"
      hx-swap="outerHTML">
    <input type="text" name="tag" required>
    <button type="submit">+</button>
</form>
```

## URL Structure

- `/` - Gallery list
- `/galleries/create/` - Create gallery
- `/galleries/<id>/` - Gallery detail
- `/galleries/<id>/edit/` - Edit gallery
- `/albums/<id>/` - Album detail
- `/pictures/<id>/` - Picture detail

## Styling

- **Tailwind CSS** via CDN
- Custom CSS in `static/gallery/css/style.css`
- Responsive design (mobile-first)

## CSRF Protection

HTMX requests include CSRF tokens automatically via:
1. Global event listener in `base.html`
2. `hx-headers` attribute on specific elements
3. Django's CSRF middleware

## Future Enhancements

- Image upload with progress bar (HTMX)
- Inline editing (HTMX)
- Infinite scroll for pictures (HTMX)
- Drag-and-drop for organizing (vanilla JS + HTMX)
- Real-time search suggestions (HTMX)
