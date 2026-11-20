"""Image generation and Cloud Storage upload tools for Traveler AI."""

import os
import uuid
from typing import Any, Dict
from google import genai
from google.cloud import storage
from google.genai import types
from google.adk.tools import ToolContext

PROJECT_ID = "qwiklabs-gcp-04-84eb67ecd5b2"
BUCKET_NAME = "traveler-ai-assets-qwiklabs-gcp-04-84eb67ecd5b2"
IMAGE_MODEL = "gemini-3.1-flash-lite-image"
IMAGE_REGION = "global"

_genai_client = None
_storage_client = None


def _get_genai_client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=IMAGE_REGION)
    return _genai_client


def _get_storage_client() -> storage.Client:
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client


async def generate_destination_image(
    prompt: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Generates a high-quality travel image or postcard using gemini-3.1-flash-lite-image in the global region.

    Saves the image as a local session artifact so it shows up in the Playground Artifacts panel,
    and uploads the image bytes to public Cloud Storage, returning the public HTTPS URL.

    Args:
        prompt: A descriptive prompt for the travel image (e.g. 'Scenic sunset over Mount Fuji with cherry blossoms', 'Eiffel Tower illuminated at night').

    Returns:
        A dictionary containing the status, public URL of the uploaded image, and artifact details.
    """
    try:
        ai_client = _get_genai_client()
        image_prompt = f"High quality travel photograph, postcard style: {prompt}"
        response = ai_client.models.generate_content(
            model=IMAGE_MODEL,
            contents=image_prompt,
        )

        image_bytes = None
        mime_type = "image/jpeg"
        for candidate in response.candidates:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.inline_data and part.inline_data.data:
                        image_bytes = part.inline_data.data
                        mime_type = part.inline_data.mime_type or "image/jpeg"
                        break
            if image_bytes:
                break

        if not image_bytes:
            return {"error": "Model did not return image data."}

        # 1. Save with tool_context.save_artifact for Playground Artifacts panel
        ext = "png" if "png" in mime_type else "jpg"
        artifact_name = f"travel_{uuid.uuid4().hex[:8]}.{ext}"
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        artifact_version = None
        try:
            artifact_version = await tool_context.save_artifact(
                filename=artifact_name,
                artifact=artifact_part,
            )
        except Exception as e:
            # Fallback if artifact service isn't active
            print(f"Artifact save note: {e}")

        # 2. Upload to public Cloud Storage bucket
        object_name = f"generated/{artifact_name}"
        storage_client = _get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(object_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_name}"

        return {
            "status": "success",
            "prompt": prompt,
            "artifact_name": artifact_name,
            "artifact_version": artifact_version,
            "public_url": public_url,
        }

    except Exception as e:
        return {"error": f"Failed to generate or upload image: {str(e)}"}


OMNI_VIDEO_MODEL = "gemini-omni-flash-preview"


async def generate_destination_video(
    prompt: str,
    tool_context: ToolContext,
) -> Dict[str, Any]:
    """Generates a short, high-quality travel video clip using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the generated video as an artifact using tool_context.save_artifact so it appears in the
    Playground Artifacts panel, and uploads the video bytes to the public Cloud Storage bucket, returning
    the public HTTPS URL.

    Args:
        prompt: A descriptive prompt for the travel video clip (e.g., 'Cinematic view of cherry blossoms drifting in front of Mount Fuji', 'Aerial drone shot of turquoise waters in Okinawa', 'Bustling night market in Shinjuku with glowing neon signs').

    Returns:
        A dictionary containing the status, public URL of the uploaded video, and artifact details.
    """
    import base64

    try:
        ai_client = _get_genai_client()
        video_prompt = f"Cinematic travel video clip: {prompt}"

        # Omni model video generation via Interactions API
        interaction = ai_client.interactions.create(
            model=OMNI_VIDEO_MODEL,
            input=[{
                "type": "user_input",
                "content": [{"type": "text", "text": video_prompt}],
            }],
            response_format=[{
                "type": "video",
                "delivery": "inline",
                "resolution": "720p",
                "duration": "3s",
            }],
        )

        output_video = getattr(interaction, "output_video", None)
        if not output_video or not getattr(output_video, "data", None):
            return {"error": "Model did not return video data or interaction failed."}

        raw_data = output_video.data
        if isinstance(raw_data, str):
            video_bytes = base64.b64decode(raw_data)
        elif isinstance(raw_data, (bytes, bytearray)):
            video_bytes = bytes(raw_data)
        else:
            return {"error": f"Unexpected video data format: {type(raw_data)}"}

        mime_type = getattr(output_video, "mime_type", None) or "video/mp4"

        # 1. Save with tool_context.save_artifact for Playground Artifacts panel
        ext = "mp4"
        artifact_name = f"travel_video_{uuid.uuid4().hex[:8]}.{ext}"
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        artifact_version = None
        try:
            artifact_version = await tool_context.save_artifact(
                filename=artifact_name,
                artifact=artifact_part,
            )
        except Exception as e:
            print(f"Artifact save note: {e}")

        # 2. Upload the same video bytes to the public Cloud Storage bucket
        object_name = f"generated_videos/{artifact_name}"
        storage_client = _get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(object_name)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_name}"

        return {
            "status": "success",
            "prompt": prompt,
            "artifact_name": artifact_name,
            "artifact_version": artifact_version,
            "public_url": public_url,
        }

    except Exception as e:
        return {"error": f"Failed to generate or upload video: {str(e)}"}
