"""Thumbnail generator using Pillow with high-CTR templates."""

from dataclasses import dataclass
from pathlib import Path
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance


@dataclass
class ThumbnailResult:
    path: str
    template_name: str
    title_text: str
    dimensions: tuple[int, int]


# Color schemes for different moods
COLOR_SCHEMES = {
    "dark_dramatic": {
        "bg": (15, 15, 25),
        "primary_text": (255, 255, 255),
        "accent": (220, 50, 50),
        "secondary": (255, 200, 50),
        "gradient_top": (30, 30, 50),
        "gradient_bottom": (10, 10, 15),
    },
    "warning": {
        "bg": (20, 10, 10),
        "primary_text": (255, 255, 255),
        "accent": (255, 60, 60),
        "secondary": (255, 200, 0),
        "gradient_top": (60, 10, 10),
        "gradient_bottom": (15, 5, 5),
    },
    "mystery": {
        "bg": (10, 10, 30),
        "primary_text": (255, 255, 255),
        "accent": (100, 100, 255),
        "secondary": (200, 200, 255),
        "gradient_top": (20, 20, 60),
        "gradient_bottom": (5, 5, 15),
    },
    "authority": {
        "bg": (10, 10, 10),
        "primary_text": (255, 255, 255),
        "accent": (255, 180, 0),
        "secondary": (200, 200, 200),
        "gradient_top": (30, 30, 30),
        "gradient_bottom": (5, 5, 5),
    },
}

THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720


class ThumbnailGenerator:
    """Generate high-CTR thumbnails with templates."""

    def __init__(self, font_dir: str | Path | None = None):
        self.font_dir = Path(font_dir) if font_dir else None
        self._setup_fonts()

    def _setup_fonts(self):
        """Load or set up fonts for thumbnail text."""
        self.fonts = {}
        try:
            # Try to load system fonts
            self.fonts["title_large"] = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72
            )
            self.fonts["title_medium"] = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56
            )
            self.fonts["subtitle"] = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36
            )
            self.fonts["number"] = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120
            )
        except (OSError, IOError):
            self.fonts["title_large"] = ImageFont.load_default()
            self.fonts["title_medium"] = ImageFont.load_default()
            self.fonts["subtitle"] = ImageFont.load_default()
            self.fonts["number"] = ImageFont.load_default()

    def generate(
        self,
        title_text: str,
        output_path: str | Path,
        template: str = "bold_text",
        color_scheme: str = "dark_dramatic",
        background_image: str | Path | None = None,
        number: int | None = None,
        subtitle: str | None = None,
    ) -> ThumbnailResult:
        """Generate a thumbnail using a template."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        colors = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["dark_dramatic"])

        if template == "bold_text":
            img = self._template_bold_text(title_text, colors, background_image)
        elif template == "numbered":
            img = self._template_numbered(title_text, colors, number or 7, background_image)
        elif template == "warning":
            img = self._template_warning(title_text, colors, background_image)
        elif template == "split":
            img = self._template_split(title_text, colors, subtitle, background_image)
        elif template == "question":
            img = self._template_question(title_text, colors, background_image)
        else:
            img = self._template_bold_text(title_text, colors, background_image)

        img.save(str(output_path), "PNG", quality=95)

        return ThumbnailResult(
            path=str(output_path),
            template_name=template,
            title_text=title_text,
            dimensions=(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT),
        )

    def _create_base(self, colors: dict, bg_image: str | Path | None = None) -> Image.Image:
        """Create base image with gradient or background."""
        if bg_image and Path(bg_image).exists():
            img = Image.open(bg_image).resize(
                (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS
            )
            # Darken background
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(0.4)
        else:
            img = Image.new("RGB", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), colors["bg"])
            draw = ImageDraw.Draw(img)
            # Draw gradient
            for y in range(THUMBNAIL_HEIGHT):
                ratio = y / THUMBNAIL_HEIGHT
                r = int(colors["gradient_top"][0] * (1 - ratio) + colors["gradient_bottom"][0] * ratio)
                g = int(colors["gradient_top"][1] * (1 - ratio) + colors["gradient_bottom"][1] * ratio)
                b = int(colors["gradient_top"][2] * (1 - ratio) + colors["gradient_bottom"][2] * ratio)
                draw.line([(0, y), (THUMBNAIL_WIDTH, y)], fill=(r, g, b))

        # Add subtle vignette
        vignette = Image.new("RGBA", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), (0, 0, 0, 0))
        vdraw = ImageDraw.Draw(vignette)
        for i in range(50):
            opacity = int(3 * i)
            vdraw.rectangle(
                [i * 2, i * 2, THUMBNAIL_WIDTH - i * 2, THUMBNAIL_HEIGHT - i * 2],
                outline=(0, 0, 0, opacity),
            )
        img = Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")

        return img

    def _draw_text_with_outline(
        self,
        draw: ImageDraw.Draw,
        position: tuple[int, int],
        text: str,
        font: ImageFont.FreeTypeFont,
        fill: tuple,
        outline_color: tuple = (0, 0, 0),
        outline_width: int = 4,
    ):
        """Draw text with an outline for readability."""
        x, y = position
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx * dx + dy * dy <= outline_width * outline_width:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        draw.text(position, text, font=font, fill=fill)

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = font.getbbox(test_line)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _template_bold_text(
        self, title: str, colors: dict, bg_image: str | Path | None = None
    ) -> Image.Image:
        """Template: Bold centered text on dark background."""
        img = self._create_base(colors, bg_image)
        draw = ImageDraw.Draw(img)

        # Draw title
        lines = self._wrap_text(title.upper(), self.fonts["title_large"], THUMBNAIL_WIDTH - 120)
        total_height = len(lines) * 85
        y_start = (THUMBNAIL_HEIGHT - total_height) // 2

        for i, line in enumerate(lines):
            bbox = self.fonts["title_large"].getbbox(line)
            text_width = bbox[2] - bbox[0]
            x = (THUMBNAIL_WIDTH - text_width) // 2
            y = y_start + i * 85
            self._draw_text_with_outline(
                draw, (x, y), line, self.fonts["title_large"], colors["primary_text"]
            )

        # Add accent bar at bottom
        draw.rectangle(
            [0, THUMBNAIL_HEIGHT - 8, THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT],
            fill=colors["accent"],
        )

        return img

    def _template_numbered(
        self,
        title: str,
        colors: dict,
        number: int,
        bg_image: str | Path | None = None,
    ) -> Image.Image:
        """Template: Large number + title text."""
        img = self._create_base(colors, bg_image)
        draw = ImageDraw.Draw(img)

        # Draw large number on the left
        num_text = str(number)
        self._draw_text_with_outline(
            draw,
            (60, THUMBNAIL_HEIGHT // 2 - 80),
            num_text,
            self.fonts["number"],
            colors["accent"],
            outline_width=6,
        )

        # Draw title on the right
        lines = self._wrap_text(title.upper(), self.fonts["title_medium"], THUMBNAIL_WIDTH - 350)
        y_start = (THUMBNAIL_HEIGHT - len(lines) * 70) // 2

        for i, line in enumerate(lines):
            self._draw_text_with_outline(
                draw,
                (300, y_start + i * 70),
                line,
                self.fonts["title_medium"],
                colors["primary_text"],
            )

        return img

    def _template_warning(
        self, title: str, colors: dict, bg_image: str | Path | None = None
    ) -> Image.Image:
        """Template: Warning/danger style with red accents."""
        img = self._create_base(colors, bg_image)
        draw = ImageDraw.Draw(img)

        # Warning stripe at top
        stripe_height = 60
        for x in range(0, THUMBNAIL_WIDTH + stripe_height, stripe_height * 2):
            draw.polygon(
                [
                    (x, 0),
                    (x + stripe_height, 0),
                    (x + stripe_height - 30, stripe_height),
                    (x - 30, stripe_height),
                ],
                fill=colors["accent"],
            )

        # Draw "WARNING" or "NEVER" text
        warning_text = "WARNING"
        bbox = self.fonts["title_medium"].getbbox(warning_text)
        w = bbox[2] - bbox[0]
        self._draw_text_with_outline(
            draw,
            ((THUMBNAIL_WIDTH - w) // 2, 80),
            warning_text,
            self.fonts["title_medium"],
            colors["accent"],
        )

        # Draw title
        lines = self._wrap_text(title.upper(), self.fonts["title_large"], THUMBNAIL_WIDTH - 100)
        y_start = 200

        for i, line in enumerate(lines):
            bbox = self.fonts["title_large"].getbbox(line)
            text_width = bbox[2] - bbox[0]
            x = (THUMBNAIL_WIDTH - text_width) // 2
            self._draw_text_with_outline(
                draw,
                (x, y_start + i * 85),
                line,
                self.fonts["title_large"],
                colors["primary_text"],
            )

        return img

    def _template_split(
        self,
        title: str,
        colors: dict,
        subtitle: str | None = None,
        bg_image: str | Path | None = None,
    ) -> Image.Image:
        """Template: Split screen comparison style."""
        img = self._create_base(colors, bg_image)
        draw = ImageDraw.Draw(img)

        # Draw vertical divider
        mid = THUMBNAIL_WIDTH // 2
        draw.line([(mid, 0), (mid, THUMBNAIL_HEIGHT)], fill=colors["accent"], width=6)

        # Left side text
        lines = self._wrap_text(title.upper(), self.fonts["title_medium"], mid - 60)
        y_start = (THUMBNAIL_HEIGHT - len(lines) * 70) // 2
        for i, line in enumerate(lines):
            self._draw_text_with_outline(
                draw,
                (30, y_start + i * 70),
                line,
                self.fonts["title_medium"],
                colors["primary_text"],
            )

        # Right side subtitle
        if subtitle:
            sub_lines = self._wrap_text(
                subtitle.upper(), self.fonts["title_medium"], mid - 60
            )
            y_start = (THUMBNAIL_HEIGHT - len(sub_lines) * 70) // 2
            for i, line in enumerate(sub_lines):
                self._draw_text_with_outline(
                    draw,
                    (mid + 30, y_start + i * 70),
                    line,
                    self.fonts["title_medium"],
                    colors["accent"],
                )

        return img

    def _template_question(
        self, title: str, colors: dict, bg_image: str | Path | None = None
    ) -> Image.Image:
        """Template: Question mark emphasis style."""
        img = self._create_base(colors, bg_image)
        draw = ImageDraw.Draw(img)

        # Large question mark in background
        self._draw_text_with_outline(
            draw,
            (THUMBNAIL_WIDTH - 300, 50),
            "?",
            self.fonts["number"],
            (*colors["accent"], ),
            outline_width=8,
        )

        # Draw title text
        lines = self._wrap_text(title.upper(), self.fonts["title_large"], THUMBNAIL_WIDTH - 200)
        y_start = (THUMBNAIL_HEIGHT - len(lines) * 85) // 2

        for i, line in enumerate(lines):
            self._draw_text_with_outline(
                draw,
                (60, y_start + i * 85),
                line,
                self.fonts["title_large"],
                colors["primary_text"],
            )

        return img

    def batch_generate(
        self,
        items: list[dict],
        output_dir: str | Path,
    ) -> list[ThumbnailResult]:
        """Generate multiple thumbnails.

        Each item should have: title, template (optional), color_scheme (optional),
        number (optional), subtitle (optional), background_image (optional).
        """
        output_dir = Path(output_dir)
        results = []

        for i, item in enumerate(items):
            filename = f"thumbnail_{i + 1:03d}.png"
            result = self.generate(
                title_text=item["title"],
                output_path=output_dir / filename,
                template=item.get("template", "bold_text"),
                color_scheme=item.get("color_scheme", "dark_dramatic"),
                background_image=item.get("background_image"),
                number=item.get("number"),
                subtitle=item.get("subtitle"),
            )
            results.append(result)

        return results
