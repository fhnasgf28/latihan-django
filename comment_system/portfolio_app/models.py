from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Post(models.Model):
    image = models.ImageField(upload_to='post_picture', default="default.png")
    caption = models.TextField(max_length=500)
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.author.username} \'s Post- {self.caption}'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.image.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)