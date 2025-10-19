import os
import re
import botocore.exceptions
import cv2
from PIL import Image
import boto3

from pydantic import BaseModel, Field
from typing import Optional

from .base import APIRequest, ResourceNotFoundError

PQAI_S3_BUCKET_NAME = os.environ['PQAI_S3_BUCKET_NAME']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)
s3 = session.resource('s3')

class DrawingRequestSchema(BaseModel):
    pn: str = Field(pattern=r'^US(RE)?\d{4,11}[AB]\d?$')
    n: Optional[int] = Field(default=1)
    w: Optional[int] = Field(default=None, ge=1, le=800)
    h: Optional[int] = Field(default=None, ge=1, le=800)

class DrawingRequest(APIRequest):
    _schema = DrawingRequestSchema

    S3_BUCKET = s3.Bucket(PQAI_S3_BUCKET_NAME)

    def _serve(self):
        tif_filepath = self._download_from_s3()
        jpg_filepath = self._convert_to_jpg(tif_filepath)

        if self.h or self.w:
            im = cv2.imread(jpg_filepath)
            im = self._downscale(im)
            cv2.imwrite(jpg_filepath, im)

        return jpg_filepath

    def _download_from_s3(self):
        s3_key = self._get_s3_key(self.pn, self.n)
        filename = s3_key.split('/').pop()
        filepath = f'/tmp/{filename}'
        try:
            self.S3_BUCKET.download_file(s3_key, filepath)
            return filepath
        except botocore.exceptions.ClientError:
            raise ResourceNotFoundError('Drawing unavailable.')

    def _get_s3_key(self, pn, n):
        if len(pn) > 13:
            return f'images/{pn}-{n}.tif'

        # For granted patents, format for storing drawings:
        # US7654321B2 -> '07654321-<n>.tif'
        pattern = r'(.+?)(A|B)\d?'
        digits = re.match(pattern, pn[2:])[1]    # extract digits
        if len(digits) == 7:
            digits = '0' + digits
        return f'images/{digits}-{n}.tif'

    def _convert_to_jpg(self, infilepath):
        im = Image.open(infilepath)
        outfilepath = infilepath.replace('.tif', '.jpg')
        im.convert("RGB").save(outfilepath, "JPEG", quality=50)
        os.remove(infilepath)
        return outfilepath

    def _downscale(self, im):
        h, w = self._get_out_dims(im)
        im = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
        return im

    def _get_out_dims(self, im):
        h, w, channels = im.shape
        r = w / h
        h_ = self.h
        w_ = self.w
        if isinstance(h_, int):
            width = max(1, int(h_*r))
            return (h_, width)
        elif isinstance(w_, int):
            height = max(1, int(w_/r))
            return (height, w_)
        return (h, w)

class ListDrawingsRequest(DrawingRequest):

    def _serve(self):
        s3_key = self._get_s3_key(self.pn, '1')
        prefix = s3_key.split('-')[0]
        indexes = [o.key.split('-')[-1].split('.')[0]
                     for o in self.S3_BUCKET.objects.filter(Prefix=prefix)]
        return {
            'drawings': indexes,
            'thumbnails': indexes
        }