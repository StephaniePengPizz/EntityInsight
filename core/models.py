from django.db import models

class WebPage(models.Model):
    url = models.URLField()
    title = models.CharField(max_length=255)
    content = models.TextField()
    source = models.CharField(max_length=100)  # Google、Bing
    publication_time = models.DateTimeField()
    credibility_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class NewsArticle(models.Model):
    web_page = models.OneToOneField(WebPage, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)  # such as Finance、Legal
    processed_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.web_page.title} - {self.category}"

class Entity(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50)  # such as Company, Person

    def __str__(self):
        return self.name

class Relationship(models.Model):
    entity1 = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='entity1')
    entity2 = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='entity2')
    relationship_type = models.CharField(max_length=100)  # such as improve
    source_article = models.ForeignKey('NewsArticle', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.entity1} {self.relationship_type} {self.entity2}"