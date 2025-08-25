#!/usr/bin/env python3
"""
Universal Video Resizing Middleware
Ensures all videos are under 600x600 dimensions before S3 upload
"""

import os
import tempfile
import subprocess
import logging
from typing import Optional, Tuple
from services.video_processing.service import video_processing_service

logger = logging.getLogger(__name__)

class VideoResizingMiddleware:
    """Middleware to resize videos to under 600x600 dimensions"""
    
    MAX_DIMENSION = 600  # Maximum width or height allowed
    
    @staticmethod
    async def resize_video_if_needed(
        input_path: str, 
        output_path: str = None
    ) -> Tuple[str, bool]:
        """
        Resize video if it exceeds 600x600 dimensions
        
        Args:
            input_path: Path to input video file
            output_path: Path for output video (optional, will generate if None)
            
        Returns:
            Tuple of (output_path, was_resized)
        """
        try:
            # Get video dimensions
            width, height = await video_processing_service._get_video_dimensions(input_path)
            if not width or not height:
                logger.warning(f"⚠️ Could not get video dimensions for {input_path}")
                return input_path, False
            
            logger.info(f"📐 Video dimensions: {width}x{height}")
            
            # Check if resizing is needed
            if width <= VideoResizingMiddleware.MAX_DIMENSION and height <= VideoResizingMiddleware.MAX_DIMENSION:
                logger.info(f"✅ Video already under {VideoResizingMiddleware.MAX_DIMENSION}x{VideoResizingMiddleware.MAX_DIMENSION}, no resizing needed")
                return input_path, False
            
            # Calculate new dimensions while maintaining aspect ratio
            new_width, new_height = VideoResizingMiddleware._calculate_resize_dimensions(width, height)
            
            logger.info(f"🔄 Resizing video from {width}x{height} to {new_width}x{new_height}")
            
            # Generate output path if not provided
            if not output_path:
                output_path = tempfile.mktemp(suffix=".mp4")
            
            # Resize video using FFmpeg
            success = await VideoResizingMiddleware._resize_video_with_ffmpeg(
                input_path, output_path, new_width, new_height
            )
            
            if success:
                logger.info(f"✅ Video resized successfully to {new_width}x{new_height}")
                return output_path, True
            else:
                logger.error(f"❌ Failed to resize video, using original")
                return input_path, False
                
        except Exception as e:
            logger.error(f"❌ Error in video resizing middleware: {str(e)}")
            return input_path, False
    
    @staticmethod
    def _calculate_resize_dimensions(width: int, height: int) -> Tuple[int, int]:
        """
        Calculate new dimensions to fit within MAX_DIMENSION while maintaining aspect ratio
        
        Args:
            width: Original width
            height: Original height
            
        Returns:
            Tuple of (new_width, new_height)
        """
        max_dim = VideoResizingMiddleware.MAX_DIMENSION
        
        # Calculate scaling factor
        scale_factor = min(max_dim / width, max_dim / height)
        
        # Calculate new dimensions
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        # Ensure dimensions are even numbers (required by some codecs)
        new_width = new_width if new_width % 2 == 0 else new_width - 1
        new_height = new_height if new_height % 2 == 0 else new_height - 1
        
        return new_width, new_height
    
    @staticmethod
    async def _resize_video_with_ffmpeg(
        input_path: str, 
        output_path: str, 
        width: int, 
        height: int
    ) -> bool:
        """
        Resize video using FFmpeg
        
        Args:
            input_path: Path to input video
            output_path: Path for output video
            width: Target width
            height: Target height
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build FFmpeg command for resizing with iOS Safari compatibility
            cmd = [
                'ffmpeg', '-y',  # Overwrite output file
                '-i', input_path,  # Input file
                '-vf', f'scale={width}:{height}',  # Resize filter
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
            
            logger.info(f"🎬 Running FFmpeg resize command: {' '.join(cmd)}")
            
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
                    logger.info(f"✅ FFmpeg resize completed: {output_path}")
                    return True
                else:
                    logger.error("❌ FFmpeg resize output file is empty or missing")
                    return False
            else:
                logger.error(f"❌ FFmpeg resize failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ FFmpeg resize timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Error in FFmpeg resize: {str(e)}")
            return False
    
    @staticmethod
    async def process_video_file(
        file_path: str, 
        cleanup_original: bool = False
    ) -> str:
        """
        Process a video file through the resizing middleware
        
        Args:
            file_path: Path to video file
            cleanup_original: Whether to delete original file after processing
            
        Returns:
            Path to processed video file
        """
        try:
            # Resize video if needed
            processed_path, was_resized = await VideoResizingMiddleware.resize_video_if_needed(file_path)
            
            # Clean up original file if it was resized and cleanup is requested
            if was_resized and cleanup_original and processed_path != file_path:
                try:
                    os.unlink(file_path)
                    logger.debug(f"🧹 Cleaned up original file: {file_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to cleanup original file {file_path}: {str(e)}")
            
            return processed_path
            
        except Exception as e:
            logger.error(f"❌ Error processing video file: {str(e)}")
            return file_path
    
    @staticmethod
    async def process_video_url(
        video_url: str, 
        user_id: str, 
        file_key: str
    ) -> Optional[str]:
        """
        Download, resize, and upload video from URL
        
        Args:
            video_url: URL of the video to process
            user_id: User ID for S3 path
            file_key: S3 file key for upload
            
        Returns:
            S3 URL of processed video or None if failed
        """
        try:
            # Download video
            temp_path = await video_processing_service._download_video(video_url)
            if not temp_path:
                logger.error("❌ Failed to download video for resizing")
                return None
            
            try:
                # Process video through resizing middleware
                processed_path = await VideoResizingMiddleware.process_video_file(temp_path, cleanup_original=True)
                
                # Upload processed video to S3
                s3_url = await video_processing_service._upload_to_s3(processed_path, file_key)
                
                return s3_url
                
            finally:
                # Clean up temporary files
                temp_files = [temp_path]
                if processed_path != temp_path:
                    temp_files.append(processed_path)
                video_processing_service._cleanup_temp_files(temp_files)
                
        except Exception as e:
            logger.error(f"❌ Error processing video URL: {str(e)}")
            return None

# Global middleware instance
video_resizing_middleware = VideoResizingMiddleware() 