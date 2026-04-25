"""YouTube upload automation using YouTube Data API v3."""

import json
from dataclasses import dataclass
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from youtube_automation.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.readonly",
]


@dataclass
class UploadResult:
    video_id: str
    url: str
    title: str
    status: str


class YouTubeUploader:
    """Upload and manage videos on YouTube."""

    def __init__(self):
        self.service = None
        self._credentials = None

    def authenticate(self, client_secrets_file: str | None = None):
        """Authenticate with YouTube API using OAuth2."""
        token_path = Path(settings.youtube_token_path)

        if token_path.exists():
            creds_data = json.loads(token_path.read_text())
            self._credentials = Credentials.from_authorized_user_info(creds_data, SCOPES)

        if not self._credentials or not self._credentials.valid:
            if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                from google.auth.transport.requests import Request

                self._credentials.refresh(Request())
            else:
                if not client_secrets_file:
                    secrets_data = {
                        "installed": {
                            "client_id": settings.youtube_client_id,
                            "client_secret": settings.youtube_client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
                        }
                    }
                    secrets_file = Path("./client_secrets_temp.json")
                    secrets_file.write_text(json.dumps(secrets_data))
                    client_secrets_file = str(secrets_file)

                flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
                self._credentials = flow.run_local_server(port=0)

            token_path.write_text(self._credentials.to_json())

        self.service = build("youtube", "v3", credentials=self._credentials)

    def upload(
        self,
        video_path: str | Path,
        title: str,
        description: str,
        tags: list[str] | None = None,
        category_id: str | None = None,
        privacy: str = "private",
        thumbnail_path: str | Path | None = None,
        scheduled_time: str | None = None,
        playlist_id: str | None = None,
    ) -> UploadResult:
        """Upload a video to YouTube."""
        if not self.service:
            self.authenticate()

        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": category_id or settings.default_category_id,
                "defaultLanguage": settings.default_language,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        if scheduled_time and privacy == "private":
            body["status"]["privacyStatus"] = "private"
            body["status"]["publishAt"] = scheduled_time

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=10 * 1024 * 1024,  # 10MB chunks
        )

        request = self.service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            _, response = request.next_chunk()

        video_id = response["id"]

        # Set thumbnail if provided
        if thumbnail_path and Path(thumbnail_path).exists():
            self.set_thumbnail(video_id, thumbnail_path)

        # Add to playlist if specified
        if playlist_id:
            self.add_to_playlist(video_id, playlist_id)

        return UploadResult(
            video_id=video_id,
            url=f"https://www.youtube.com/watch?v={video_id}",
            title=title,
            status=body["status"]["privacyStatus"],
        )

    def set_thumbnail(self, video_id: str, thumbnail_path: str | Path):
        """Set a custom thumbnail for a video."""
        if not self.service:
            self.authenticate()

        media = MediaFileUpload(str(thumbnail_path), mimetype="image/png")
        self.service.thumbnails().set(
            videoId=video_id,
            media_body=media,
        ).execute()

    def add_to_playlist(self, video_id: str, playlist_id: str):
        """Add a video to a playlist."""
        if not self.service:
            self.authenticate()

        self.service.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                },
            },
        ).execute()

    def create_playlist(self, title: str, description: str = "", privacy: str = "public") -> str:
        """Create a new playlist and return its ID."""
        if not self.service:
            self.authenticate()

        response = (
            self.service.playlists()
            .insert(
                part="snippet,status",
                body={
                    "snippet": {"title": title, "description": description},
                    "status": {"privacyStatus": privacy},
                },
            )
            .execute()
        )

        return response["id"]

    def get_video_analytics(self, video_id: str) -> dict:
        """Get basic analytics for a video."""
        if not self.service:
            self.authenticate()

        response = (
            self.service.videos()
            .list(
                part="statistics,snippet",
                id=video_id,
            )
            .execute()
        )

        if not response.get("items"):
            return {}

        item = response["items"][0]
        stats = item.get("statistics", {})

        return {
            "title": item["snippet"]["title"],
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "favorites": int(stats.get("favoriteCount", 0)),
        }

    def get_channel_stats(self) -> dict:
        """Get channel statistics."""
        if not self.service:
            self.authenticate()

        response = (
            self.service.channels()
            .list(
                part="statistics,snippet",
                mine=True,
            )
            .execute()
        )

        if not response.get("items"):
            return {}

        item = response["items"][0]
        stats = item.get("statistics", {})

        return {
            "title": item["snippet"]["title"],
            "subscribers": int(stats.get("subscriberCount", 0)),
            "total_views": int(stats.get("viewCount", 0)),
            "total_videos": int(stats.get("videoCount", 0)),
        }

    def update_video(
        self,
        video_id: str,
        title: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
    ):
        """Update video metadata."""
        if not self.service:
            self.authenticate()

        # Get current video data
        current = (
            self.service.videos()
            .list(
                part="snippet",
                id=video_id,
            )
            .execute()
        )

        if not current.get("items"):
            raise ValueError(f"Video not found: {video_id}")

        snippet = current["items"][0]["snippet"]

        if title:
            snippet["title"] = title
        if description:
            snippet["description"] = description
        if tags:
            snippet["tags"] = tags

        self.service.videos().update(
            part="snippet",
            body={"id": video_id, "snippet": snippet},
        ).execute()
