#!/usr/bin/env python3
"""
Video Processing Service for iDance Backend
Handles video cropping and processing using FFmpeg
"""

import os
import tempfile
import subprocess
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class VideoProcessingService:
    """Service for processing and cropping videos"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'idance')
        
    async def crop_video(
        self, 
        input_url: str, 
        crop_data: Dict[str, Any], 
        output_file_key: str
    ) -> Optional[str]:
        """
        Crop video based on crop data and upload to S3
        
        Args:
            input_url: URL of the original video
            crop_data: Dictionary containing crop settings
            output_file_key: S3 file key for the processed video
            
        Returns:
            URL of the processed video or None if failed
        """
        try:
            logger.info(f"🎬 Starting video cropping for {input_url}")
            
            # Download video to temporary file
            temp_input_path = await self._download_video(input_url)
            if not temp_input_path:
                logger.error("❌ Failed to download video")
                return None
            
            # Create temporary output file
            temp_output_path = tempfile.mktemp(suffix=".mp4")
            
            try:
                # Crop video using FFmpeg
                success = await self._crop_video_with_ffmpeg(
                    temp_input_path, 
                    temp_output_path, 
                    crop_data
                )
                
                if not success:
                    logger.error("❌ Failed to crop video with FFmpeg")
                    return None
                
                # Upload cropped video to S3
                processed_url = await self._upload_to_s3(temp_output_path, output_file_key)
                
                if processed_url:
                    logger.info(f"✅ Video cropping completed: {processed_url}")
                    return processed_url
                else:
                    logger.error("❌ Failed to upload cropped video to S3")
                    return None
                    
            finally:
                # Clean up temporary files
                self._cleanup_temp_files([temp_input_path, temp_output_path])
                
        except Exception as e:
            logger.error(f"❌ Error in video cropping: {str(e)}")
            return None
    
    async def _download_video(self, url: str) -> Optional[str]:
        """Download video from URL to temporary file"""
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            temp_path = temp_file.name
            
            # Download video content
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            
            temp_file.close()
            
            # Verify file was downloaded
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                logger.info(f"✅ Downloaded video: {temp_path} ({os.path.getsize(temp_path)} bytes)")
                return temp_path
            else:
                logger.error("❌ Downloaded file is empty or missing")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to download video from {url}: {str(e)}")
            return None
    
    async def _crop_video_with_ffmpeg(
        self, 
        input_path: str, 
        output_path: str, 
        crop_data: Dict[str, Any]
    ) -> bool:
        """Crop video using FFmpeg based on crop template"""
        try:
            crop_template = crop_data.get('cropTemplate', 'square')
            aspect_ratio = crop_data.get('aspectRatio', 1.0)
            
            # Get video dimensions first
            video_width, video_height = await self._get_video_dimensions(input_path)
            if not video_width or not video_height:
                logger.error("❌ Failed to get video dimensions")
                return False
            
            # Calculate crop dimensions based on template
            if crop_template == 'square':
                # Crop to square (1:1 aspect ratio) - center crop
                crop_size = min(video_width, video_height)
                x_offset = (video_width - crop_size) // 2
                y_offset = (video_height - crop_size) // 2
                filter_complex = f"crop={crop_size}:{crop_size}:{x_offset}:{y_offset}"
            elif crop_template == 'portrait':
                # Crop to portrait (9:16 aspect ratio) - center crop
                crop_width = video_width
                crop_height = int(video_width * 16 / 9)
                if crop_height > video_height:
                    crop_height = video_height
                    crop_width = int(video_height * 9 / 16)
                x_offset = (video_width - crop_width) // 2
                y_offset = (video_height - crop_height) // 2
                filter_complex = f"crop={crop_width}:{crop_height}:{x_offset}:{y_offset}"
            elif crop_template == 'landscape':
                # Crop to landscape (16:9 aspect ratio) - center crop
                crop_width = int(video_height * 16 / 9)
                crop_height = video_height
                if crop_width > video_width:
                    crop_width = video_width
                    crop_height = int(video_width * 9 / 16)
                x_offset = (video_width - crop_width) // 2
                y_offset = (video_height - crop_height) // 2
                filter_complex = f"crop={crop_width}:{crop_height}:{x_offset}:{y_offset}"
            else:
                # Default to square
                crop_size = min(video_width, video_height)
                x_offset = (video_width - crop_size) // 2
                y_offset = (video_height - crop_size) // 2
                filter_complex = f"crop={crop_size}:{crop_size}:{x_offset}:{y_offset}"
            
            logger.info(f"📐 Video dimensions: {video_width}x{video_height}, Crop filter: {filter_complex}")
            
            # Build FFmpeg command with iOS Safari compatibility
            cmd = [
                'ffmpeg', '-y',  # Overwrite output file
                '-i', input_path,  # Input file
                '-vf', filter_complex,  # Video filter
                '-c:v', 'libx264',  # Video codec
                '-preset', 'medium',  # Encoding preset
                '-crf', '23',  # Quality setting
                '-profile:v', 'baseline',  # iOS Safari compatibility
                '-level', '3.0',  # iOS Safari compatibility
                '-pix_fmt', 'yuv420p',  # iOS Safari compatibility
                '-c:a', 'aac',  # Audio codec
                '-b:a', '128k',  # Audio bitrate
                '-movflags', '+faststart',  # Web streaming optimization
                output_path  # Output file
            ]
            
            logger.info(f"🎬 Running FFmpeg command: {' '.join(cmd)}")
            
            # Execute FFmpeg command
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Verify output file was created
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"✅ FFmpeg processing completed: {output_path}")
                    return True
                else:
                    logger.error("❌ FFmpeg output file is empty or missing")
                    return False
            else:
                logger.error(f"❌ FFmpeg failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ FFmpeg processing timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Error in FFmpeg processing: {str(e)}")
            return False
    
    async def _get_video_dimensions(self, video_path: str) -> tuple:
        """Get video width and height using ffprobe"""
        try:
            cmd = [
                'ffprobe', 
                '-v', 'quiet', 
                '-select_streams', 'v:0', 
                '-show_entries', 'stream=width,height', 
                '-of', 'csv=p=0', 
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                dimensions = result.stdout.strip().split(',')
                if len(dimensions) == 2:
                    width = int(dimensions[0])
                    height = int(dimensions[1])
                    return width, height
                else:
                    logger.error(f"❌ Unexpected ffprobe output: {result.stdout}")
                    return None, None
            else:
                logger.error(f"❌ Failed to get video dimensions: {result.stderr}")
                return None, None
                
        except Exception as e:
            logger.error(f"❌ Error getting video dimensions: {str(e)}")
            return None, None
    
    async def _upload_to_s3(self, file_path: str, file_key: str) -> Optional[str]:
        """Upload file to S3 and return the URL"""
        try:
            # Upload file to S3 without ACL (bucket has ACL disabled)
            self.s3_client.upload_file(
                file_path, 
                self.bucket_name, 
                file_key,
                ExtraArgs={
                    'ContentType': 'video/mp4'
                    # Removed ACL setting since bucket has ACL disabled
                }
            )
            
            # Generate URL
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{file_key}"
            logger.info(f"✅ Uploaded to S3: {url}")
            return url
            
        except ClientError as e:
            logger.error(f"❌ S3 upload failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Error uploading to S3: {str(e)}")
            return None
    
    def _cleanup_temp_files(self, file_paths: list):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.debug(f"🧹 Cleaned up: {file_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to cleanup {file_path}: {str(e)}")
    
    def get_video_duration(self, video_path: str) -> float:
        """Get video duration using ffprobe"""
        try:
            cmd = [
                'ffprobe', 
                '-v', 'quiet', 
                '-show_entries', 'format=duration', 
                '-of', 'csv=p=0', 
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                return duration
            else:
                logger.warning(f"⚠️ Failed to get video duration: {result.stderr}")
                return 0.0
                
        except Exception as e:
            logger.warning(f"⚠️ Error getting video duration: {str(e)}")
            return 0.0

# Global service instance
video_processing_service = VideoProcessingService() 