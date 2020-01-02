from os import path as os_path
from secrets import token_urlsafe
from django.db import models
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from monero.address import address
from PIL import Image, ExifTags
from io import BytesIO
from core.monero import AuctionDaemon


def address_is_valid_monero(value):
    try:
        address(value)
        return True
    except ValueError:
        raise ValidationError(
            _('%(value)s is an invalid Monero address'),
            params={'value': value},
        )

class Item(models.Model):
    owner = models.ForeignKey(User, related_name='owner', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    list_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    description = models.TextField(max_length=500)
    ask_price_xmr = models.FloatField()
    available = models.BooleanField(default=True)
    payout_address = models.CharField(max_length=100, validators=[address_is_valid_monero])

    def __str__(self):
        return f"{self.id} - {self.owner} - {self.name}"


class ItemImage(models.Model):
    item = models.ForeignKey(Item, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='%Y/%m/%d')
    thumbnail = models.ImageField(upload_to='%Y/%m/%d')

    def save(self, *args, **kwargs):
        self.correct_image()
        self.copy_to_storage()
        super(ItemImage, self).save(*args, **kwargs)

    def copy_to_storage(self):
        pass

    def correct_image(self):
        try:
            # Open image and set some variables
            img = Image.open(self.image)
            img_format = img.format
            max_size = (800, 800)
            thumb_size = (150, 150)
            file_ext = os_path.splitext(self.image.name)[1]
            random_str = token_urlsafe(12)
            img_name = f'{self.item.id}-{random_str}.%s{file_ext}'
            img_bytes = BytesIO()
            thumb_bytes = BytesIO()

            # If image contains exif check for orientation and rotate
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    img_exif = img._getexif()
                    if img_exif:
                        if orientation in img_exif:
                            image_orientation = img_exif[orientation]
                            if image_orientation == 3:
                                img = img.rotate(180, expand=True)
                            if image_orientation == 6:
                                img = img.rotate(-90, expand=True)
                            if image_orientation == 8:
                                img = img.rotate(90, expand=True)

            # Store a copy of the image for thumbnail
            thumb = img.copy()

            # Correct the image size to safe maximums
            img.thumbnail(max_size, Image.ANTIALIAS)
            img.save(img_bytes, format=img_format, quality=80)
            self.image = InMemoryUploadedFile(
                img_bytes,
                'ImageField',
                img_name % 'full',
                self.image.file.content_type,
                img.size,
                self.image.file.charset
            )

            # Create thumbnail from image
            thumb.thumbnail(thumb_size, Image.ANTIALIAS)
            thumb.save(thumb_bytes, format=img_format, quality=80)
            self.thumbnail = InMemoryUploadedFile(
                thumb_bytes,
                'ImageField',
                img_name % 'thumbnail',
                self.image.file.content_type,
                img.size,
                self.image.file.charset
            )

            thumb.close()
            img.close()
        except:
            raise Exception('Unable to correct image size')

    def __str__(self):
        return f"{self.id} - {self.item.name} - {self.id}"
