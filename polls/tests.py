import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User, Permission

from .models import Question, Choice


class QuestionModelTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


def create_question(question_text, days):
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


def create_choice(question, choice_text='default choice'):
    return Choice.objects.create(question=question, choice_text=choice_text, votes=0)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question(self):
        question = create_question(question_text="Past question.", days=-30)
        create_choice(question)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(response.context['latest_question_list'], [question])

    def test_future_question(self):
        question = create_question(question_text="Future question.", days=30)
        create_choice(question)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question(self):
        past_question = create_question(question_text="Past question.", days=-30)
        create_choice(past_question)
        future_question = create_question(question_text="Future question.", days=30)
        create_choice(future_question)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(response.context['latest_question_list'], [past_question])

    def test_two_past_questions(self):
        question1 = create_question(question_text="Past question 1", days=-30)
        create_choice(question1)
        question2 = create_question(question_text="Past question 2", days=-5)
        create_choice(question2)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(response.context['latest_question_list'], [question2, question1])

    def test_past_question_without_choice(self):
        question = create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(response.context['latest_question_list'], [])


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        future_question = create_question(question_text='Future question', days=5)
        create_choice(future_question)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        past_question = create_question(question_text='Past Question.', days=-5)
        create_choice(past_question)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

    def test_future_question_without_choice(self):
        past_question = create_question(question_text='Future question', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class QuestionResultsViewTests(TestCase):
    def test_poll_does_not_exist(self):
        response = self.client.get(reverse('polls:results', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 404)

    def test_poll_exist(self):
        question = create_question(question_text="Past question.", days=-30)
        create_choice(question)
        response = self.client.get(reverse('polls:results', kwargs={'pk': question.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, question.question_text)

    def test_poll_future(self):
        future_question = create_question(question_text="Future question.", days=5)
        create_choice(future_question)
        response = self.client.get(reverse('polls:results', kwargs={'pk': future_question.pk}))
        self.assertEqual(response.status_code, 404)

    def test_poll_exist_without_choice(self):
        question = create_question(question_text="Past question.", days=-20)
        response = self.client.get(reverse('polls:results', kwargs={'pk': question.pk}))
        self.assertEqual(response.status_code, 404)


class QuestionDetailViewTestsUsers(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.past_question = create_question(question_text='Past Question.', days=-5)
        self.url = reverse('polls:detail', args=(self.past_question.id,))

    def test_admin_user(self):
        self.user.is_superuser = True
        self.user.save()
        login = self.client.login(username='testuser', password='12345')
        response = self.client.get(self.url)
        self.assertContains(response, self.past_question.question_text)

    def test_non_admin_user(self):
        login = self.client.login(username='testuser', password='12345')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
