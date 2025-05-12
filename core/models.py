from django.db import models

class WebPage(models.Model):
    url = models.URLField()
    title = models.CharField(max_length=255)
    source = models.CharField(max_length=100)  # Google、Bing
    publication_time = models.DateTimeField(null=True, blank=True)
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
    frequency = models.IntegerField()

    def __str__(self):
        return self.name

class Relationship(models.Model):
    source = models.ForeignKey(Entity, related_name='outgoing_relations', on_delete=models.CASCADE)
    target = models.ForeignKey(Entity, related_name='incoming_relations', on_delete=models.CASCADE)
    relation_type = models.CharField(max_length=200, null=True, blank=True)
    weight = models.FloatField()
    source_article = models.ForeignKey('NewsArticle', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.source} {self.relation_type} {self.target}"