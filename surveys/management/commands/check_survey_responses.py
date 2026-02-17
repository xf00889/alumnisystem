from django.core.management.base import BaseCommand
from surveys.models import Survey, SurveyResponse, ResponseAnswer


class Command(BaseCommand):
    help = 'Check survey responses in the database'

    def add_arguments(self, parser):
        parser.add_argument('survey_id', type=int, help='Survey ID to check')

    def handle(self, *args, **options):
        survey_id = options['survey_id']
        
        try:
            survey = Survey.objects.get(id=survey_id)
            self.stdout.write(self.style.SUCCESS(f'\n=== Survey: {survey.title} (ID: {survey.id}) ===\n'))
            
            # Get all questions
            questions = survey.questions.all()
            self.stdout.write(f'Total Questions: {questions.count()}\n')
            for q in questions:
                self.stdout.write(f'  Q{q.id}: {q.question_text} (Type: {q.question_type})')
            
            # Get all responses
            responses = SurveyResponse.objects.filter(survey=survey)
            self.stdout.write(f'\nTotal Responses: {responses.count()}\n')
            
            for response in responses:
                self.stdout.write(self.style.WARNING(f'\n--- Response ID: {response.id} ---'))
                self.stdout.write(f'Alumni: {response.alumni.user.get_full_name()}')
                self.stdout.write(f'Submitted: {response.submitted_at}')
                
                # Get all answers for this response
                answers = ResponseAnswer.objects.filter(response=response)
                self.stdout.write(f'Total Answers: {answers.count()}\n')
                
                for answer in answers:
                    self.stdout.write(f'  Question ID: {answer.question.id}')
                    self.stdout.write(f'  Question: {answer.question.question_text}')
                    self.stdout.write(f'  Type: {answer.question.question_type}')
                    self.stdout.write(f'  text_answer: {answer.text_answer}')
                    self.stdout.write(f'  rating_value: {answer.rating_value}')
                    self.stdout.write(f'  selected_option: {answer.selected_option}')
                    self.stdout.write('')
                    
        except Survey.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Survey with ID {survey_id} does not exist'))
