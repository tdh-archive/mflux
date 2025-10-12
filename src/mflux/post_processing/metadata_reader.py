"""Metadata reader for extracting and parsing image metadata."""

import json
import logging
from pathlib import Path

import piexif
import PIL.Image

log = logging.getLogger(__name__)


class MetadataReader:
    """Reads and parses metadata from MFLUX generated images."""

    @staticmethod
    def read_exif_metadata(image_path: str | Path) -> dict | None:
        """
        Extract EXIF metadata from an image.

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary containing parsed EXIF metadata, or None if not found
        """
        try:
            img = PIL.Image.open(image_path)
            exif_bytes = img.info.get("exif")

            if not exif_bytes:
                return None

            exif_dict = piexif.load(exif_bytes)
            user_comment = exif_dict["Exif"].get(0x9286, b"")

            if user_comment:
                # Try to parse as JSON (strip the ASCII prefix if present)
                if user_comment.startswith(b"ASCII\x00\x00\x00"):
                    metadata_str = user_comment[8:].decode("utf-8")
                else:
                    metadata_str = user_comment.decode("utf-8")
                return json.loads(metadata_str)

            return None

        except Exception as e:
            log.debug(f"Error reading EXIF metadata: {e}")
            return None

    @staticmethod
    def read_xmp_metadata(image_path: str | Path) -> dict | None:
        """
        Extract XMP metadata from an image.

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary containing parsed XMP metadata, or None if not found
        """
        try:
            img = PIL.Image.open(image_path)
            xmp_data = img.info.get("XML:com.adobe.xmp")

            if not xmp_data:
                return None

            # Parse XMP XML to extract key fields
            xmp_dict = {}

            # Simple XML parsing for common fields
            fields = {
                "description": "<dc:description><rdf:Alt><rdf:li xml:lang=\"x-default\">",
                "creator": "<dc:creator><rdf:Seq><rdf:li>",
                "rights": "<dc:rights><rdf:Alt><rdf:li xml:lang=\"x-default\">",
                "creator_tool": "<xmp:CreatorTool>",
                "category": "<photoshop:Category>",
                "credit": "<photoshop:Credit>",
                "seed": "<mflux:seed>",
                "steps": "<mflux:steps>",
                "guidance": "<mflux:guidance>",
                "model": "<mflux:model>",
                "loras": "<mflux:loras>",
                "generation_time": "<mflux:generationTime>",
            }

            for key, start_tag in fields.items():
                if start_tag in xmp_data:
                    start_idx = xmp_data.index(start_tag) + len(start_tag)
                    # Find the closing tag
                    if key in ["description", "rights"]:
                        end_tag = "</rdf:li>"
                    elif key == "creator":
                        end_tag = "</rdf:li>"
                    else:
                        # Extract tag name from start_tag
                        tag_name = start_tag.split(":")[1].rstrip(">")
                        end_tag = f"</{start_tag.split(':')[0]}:{tag_name}>"

                    end_idx = xmp_data.index(end_tag, start_idx)
                    value = xmp_data[start_idx:end_idx]
                    xmp_dict[key] = value

            return xmp_dict if xmp_dict else None

        except Exception as e:
            log.debug(f"Error reading XMP metadata: {e}")
            return None

    @staticmethod
    def read_all_metadata(image_path: str | Path) -> dict:
        """
        Read all available metadata from an image.

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary with 'exif' and 'xmp' keys containing metadata
        """
        return {
            "exif": MetadataReader.read_exif_metadata(image_path),
            "xmp": MetadataReader.read_xmp_metadata(image_path),
        }

