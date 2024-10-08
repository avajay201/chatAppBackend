from PIL import Image
import ffmpeg
from django.core.files.uploadedfile import UploadedFile


def validate_image(file: UploadedFile):
    '''Validate that the image file is not corrupted.'''
    try:
        content_type = file.content_type
        if content_type not in ('image/png', 'image/jpeg', 'image/jpg'):
            return
        img = Image.open(file)
        img.verify()
        return True
    except Exception as err:
        print('Image validating error:', err)

def validate_video(file: UploadedFile):
    '''Validate that the video file is not corrupted.'''
    try:
        content_type = file.content_type
        print('content_type>>>', content_type)
        if content_type not in ('video/mp4'):
            return
        probe = ffmpeg.probe(file.temporary_file_path())
        if 'streams' not in probe or len(probe['streams']) == 0:
            return
        return True
    except Exception as err:
        print('Video validating error:', err)
