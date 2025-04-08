from django.db import models

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def edit(self, name, description, image):
        self.name = name 
        self.description = description
        self.image = image
        self.save()
    
    def short_description(self):
        words = self.description.split()
        if len(words) > 50:
            return " ".join(words[:50]) + "..."
        else:
            return self.description