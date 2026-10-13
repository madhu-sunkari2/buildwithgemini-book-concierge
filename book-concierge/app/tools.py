# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from typing import Any, Dict, List, Optional
from google.cloud import firestore

# Hardcoded project ID as required for Agent Platform compatibility
PROJECT_ID = "qwiklabs-gcp-04-b5e9e11cd71a"


def _get_db() -> firestore.Client:
    return firestore.Client(project=PROJECT_ID)


def list_books(
    genre: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """List books from the catalog or reading list with optional filtering.

    Args:
        genre: Optional genre filter (e.g., 'Science Fiction', 'Fantasy', 'Self-Help').
        status: Optional reading status filter ('want_to_read', 'reading', 'read').
        limit: Maximum number of books to return (default: 10).

    Returns:
        A list of book dictionaries matching the criteria.
    """
    db = _get_db()
    query = db.collection("books")

    if status:
        query = query.where(field_path="status", op_string="==", value=status)

    docs = query.limit(limit * 2 if genre else limit).stream()
    books: List[Dict[str, Any]] = []

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        if genre and genre.lower() not in str(data.get("genre", "")).lower():
            continue
        books.append(data)
        if len(books) >= limit:
            break

    return books


def search_books(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for books in the catalog by title, author, or synopsis keywords.

    Args:
        query: Search term or keyword (e.g., 'space', 'Andy Weir', 'fiction').
        limit: Maximum number of search results to return.

    Returns:
        A list of matching book dictionaries.
    """
    db = _get_db()
    docs = db.collection("books").stream()
    query_lower = query.lower()
    matches: List[Dict[str, Any]] = []

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        title = str(data.get("title", "")).lower()
        author = str(data.get("author", "")).lower()
        synopsis = str(data.get("synopsis", "")).lower()
        genre = str(data.get("genre", "")).lower()

        if (
            query_lower in title
            or query_lower in author
            or query_lower in synopsis
            or query_lower in genre
        ):
            matches.append(data)
            if len(matches) >= limit:
                break

    return matches


def get_book_details(book_id: str) -> Dict[str, Any]:
    """Retrieve detailed information about a specific book by its ID.

    Args:
        book_id: The document ID of the book (e.g. 'project-hail-mary').

    Returns:
        The book data dictionary, or an error dictionary if not found.
    """
    db = _get_db()
    doc_ref = db.collection("books").document(book_id)
    doc = doc_ref.get()
    if not doc.exists:
        return {"error": f"Book with ID '{book_id}' was not found in the catalog."}
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def add_or_update_book(
    title: str,
    author: str,
    genre: str,
    synopsis: str,
    pages: int = 0,
    rating: float = 0.0,
    status: str = "want_to_read",
    notes: str = "",
    book_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a new book to the catalog/reading list or update an existing one.

    Args:
        title: The title of the book.
        author: The author of the book.
        genre: The genre of the book (e.g., 'Science Fiction', 'Thriller').
        synopsis: A brief synopsis or summary of the book.
        pages: Total number of pages (optional).
        rating: User rating from 1.0 to 5.0 (optional).
        status: Reading status ('want_to_read', 'reading', 'read'). Defaults to 'want_to_read'.
        notes: Personal thoughts, recommendations, or review notes.
        book_id: Optional ID. If omitted, generated from title.

    Returns:
        A dictionary confirming the book ID and saved status.
    """
    db = _get_db()
    if not book_id:
        book_id = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

    book_data = {
        "id": book_id,
        "title": title,
        "author": author,
        "genre": genre,
        "synopsis": synopsis,
        "pages": pages,
        "rating": rating,
        "status": status,
        "notes": notes,
    }

    doc_ref = db.collection("books").document(book_id)
    doc_ref.set(book_data, merge=True)
    return {"success": True, "message": f"Saved book '{title}' with ID '{book_id}'.", "book": book_data}


def update_reading_status(book_id: str, status: str, rating: Optional[float] = None, notes: Optional[str] = None) -> Dict[str, Any]:
    """Update reading status, rating, or notes for a book.

    Args:
        book_id: The ID of the book to update (e.g. 'project-hail-mary').
        status: New status ('want_to_read', 'reading', 'read').
        rating: Optional updated rating from 1.0 to 5.0.
        notes: Optional updated personal notes or review.

    Returns:
        A dictionary confirming the update or error.
    """
    db = _get_db()
    doc_ref = db.collection("books").document(book_id)
    doc = doc_ref.get()
    if not doc.exists:
        return {"error": f"Book with ID '{book_id}' not found."}

    update_fields: Dict[str, Any] = {"status": status}
    if rating is not None:
        update_fields["rating"] = rating
    if notes is not None:
        update_fields["notes"] = notes

    doc_ref.update(update_fields)
    return {"success": True, "message": f"Updated book '{book_id}' status to '{status}'.", "updated_fields": update_fields}


def search_online_books(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search online library catalog (Open Library) for books by title, author, or subject.

    Use this when the user asks about a book not in their local collection,
    or wants to discover new titles, publish dates, and authors.

    Args:
        query: Search keywords, book title, author, or subject (e.g., 'Frank Herbert', 'Dune').
        limit: Maximum number of results to return (default: 5).

    Returns:
        A list of matching books with title, author, first publish year, and subjects.
    """
    import json
    import urllib.parse
    import urllib.request

    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://openlibrary.org/search.json?q={encoded_query}&limit={limit}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "BookConcierge/1.0 (adk-agent)"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        return [{"error": f"Failed to fetch books online: {e}"}]

    results: List[Dict[str, Any]] = []
    for doc in data.get("docs", [])[:limit]:
        title = doc.get("title", "Unknown Title")
        authors = doc.get("author_name", ["Unknown Author"])
        year = doc.get("first_publish_year")
        subjects = doc.get("subject", [])[:3]
        cover_id = doc.get("cover_i")

        results.append({
            "title": title,
            "author": ", ".join(authors[:2]),
            "first_publish_year": year,
            "subjects": subjects,
            "cover_url": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None,
        })

    return results


def get_trending_books(limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch currently trending and popular books across global readers from Open Library.

    Use this when the user asks for recommendations, popular titles right now,
    or what others are currently reading.

    Args:
        limit: Number of trending titles to retrieve (default: 5).

    Returns:
        A list of currently trending books with title, authors, first publish year, and cover image.
    """
    import json
    import urllib.request

    url = f"https://openlibrary.org/trending/daily.json?limit={limit}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "BookConcierge/1.0 (adk-agent)"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        return [{"error": f"Failed to fetch trending books: {e}"}]

    trending_books: List[Dict[str, Any]] = []
    for item in data.get("works", [])[:limit]:
        title = item.get("title", "Unknown Title")
        authors = item.get("author_name", ["Unknown Author"])
        year = item.get("first_publish_year")
        cover_id = item.get("cover_i")

        trending_books.append({
            "title": title,
            "author": ", ".join(authors[:2]),
            "first_publish_year": year,
            "cover_url": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None,
        })

    return trending_books


def generate_book_cover(
    title: str,
    description: str,
    tool_context: Any = None,
) -> Dict[str, Any]:
    """Generate custom book cover art using gemini-3.1-flash-lite-image in the global region.

    Saves the image as a session artifact and uploads it to Google Cloud Storage,
    returning the public HTTPS URL.

    Args:
        title: The title of the book.
        description: Description of the book's theme, mood, or artistic style for the cover.
        tool_context: ADK ToolContext injected automatically by the framework.

    Returns:
        A dictionary containing the title, public image URL, and status.
    """
    import re
    import time
    from google import genai
    from google.genai import types
    from google.cloud import storage

    bucket_name = "book-concierge-qwiklabs-gcp-04-b5e9e11cd71a"
    project_id = "qwiklabs-gcp-04-b5e9e11cd71a"

    prompt = (
        f"Artistic book cover illustration for '{title}'. "
        f"Visual style and theme: {description}. "
        "Professional book cover art, high resolution, stunning composition, aesthetic typography-free artwork."
    )

    client = genai.Client(vertexai=True, location="global")
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
    )

    image_bytes = None
    mime_type = "image/jpeg"
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            image_bytes = part.inline_data.data
            mime_type = part.inline_data.mime_type or "image/jpeg"
            break

    if not image_bytes:
        return {"error": f"No image could be generated for '{title}'."}

    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    timestamp = int(time.time())
    ext = "png" if "png" in mime_type else "jpg"
    filename = f"cover_{slug}_{timestamp}.{ext}"

    # 1. Save artifact for playground UI
    if tool_context and hasattr(tool_context, "save_artifact"):
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(
            filename=filename,
            artifact=artifact_part,
            custom_metadata={"title": title, "type": "book_cover"},
        )

    # 2. Upload to public Cloud Storage bucket
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    object_path = f"covers/{filename}"
    blob = bucket.blob(object_path)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{object_path}"

    return {
        "success": True,
        "title": title,
        "filename": filename,
        "image_url": public_url,
        "message": f"Generated custom cover art for '{title}'.",
    }


def generate_book_trailer(
    title: str,
    theme: Optional[str] = None,
    tool_context: Optional[Any] = None,
) -> Dict[str, Any]:
    """Generate a short cinematic video book trailer using Google's Omni model (gemini-omni-flash-preview).

    Args:
        title: Title of the book or literary work to generate a video trailer for.
        theme: Optional visual style, mood, or cinematic details (e.g., 'cyberpunk neon city', 'dark gothic fantasy castle', 'peaceful misty forest').
        tool_context: ADK ToolContext injected automatically by the framework.

    Returns:
        A dictionary containing the title, public video URL, filename, and status message.
    """
    import base64
    import re
    import time
    from google import genai
    from google.genai import types
    from google.cloud import storage

    bucket_name = "book-concierge-qwiklabs-gcp-04-b5e9e11cd71a"
    project_id = "qwiklabs-gcp-04-b5e9e11cd71a"

    prompt_details = theme if theme else "cinematic atmosphere, dramatic lighting, rich literary tone"
    prompt = (
        f"Cinematic video book teaser trailer for '{title}'. "
        f"Visual style and atmosphere: {prompt_details}. "
        "Smooth camera motion, high production quality, atmospheric lighting, evocative scene."
    )

    client = genai.Client(vertexai=True, location="global")
    interaction = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=prompt,
    )

    video_bytes = None
    if hasattr(interaction, "output_video") and interaction.output_video and getattr(interaction.output_video, "data", None):
        video_bytes = base64.b64decode(interaction.output_video.data)
    elif hasattr(interaction, "steps"):
        for step in interaction.steps or []:
            if getattr(step, "type", None) == "model_output":
                for content in getattr(step, "content", []) or []:
                    if getattr(content, "type", None) == "video" and getattr(content, "data", None):
                        video_bytes = base64.b64decode(content.data)
                        break

    if not video_bytes:
        return {"error": f"No video could be generated for '{title}'."}

    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    timestamp = int(time.time())
    filename = f"trailer_{slug}_{timestamp}.mp4"
    mime_type = "video/mp4"

    # 1. Save artifact for playground UI
    if tool_context and hasattr(tool_context, "save_artifact"):
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        tool_context.save_artifact(
            filename=filename,
            artifact=artifact_part,
            custom_metadata={"title": title, "type": "book_trailer"},
        )

    # 2. Upload to public Cloud Storage bucket
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    object_path = f"trailers/{filename}"
    blob = bucket.blob(object_path)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{object_path}"

    return {
        "success": True,
        "title": title,
        "filename": filename,
        "video_url": public_url,
        "message": f"Generated short video teaser trailer for '{title}'.",
    }

