import datetime

from django.db import models
from django.utils import timezone
from django.contrib import admin
from django.db.models.signals import post_save
from django.dispatch import receiver


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

    def __str__(self):
        return self.question_text

    @admin.display(
        boolean=True,
        ordering='pub_date',
        description='Published recently?',
    )
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now


@receiver(post_save, sender=Question)
def question_created_handler(sender, instance, created, *args, **kwargs):
    if created:
        print("created", instance.question_text)
    else:
        print(instance.question_text, "was just saved")


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text
