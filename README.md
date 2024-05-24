# jyutping-learning-site
Django project for learning Cantonese using the Jyutping romanisation. Import your own words, sentences and audio files as you learn them and play randomly generated quizes.

## Set up (like any standard Django project):
- On local:
  - Install python and pip.
  - (optional) Install venv and enter a virtual environment.
  - Install django (optional: in a virtual environment).
  - Install other libraries in `requirements.txt`.
  - `pip install django`.
  - `pip install -r requirements.txt`
  - `python manage.py migrate`
  - `python manage.py createsuperuser`
  - `python manage.py runserver`
- On live:
  - Follow a guide for configuring a Django project on your preferred cloud hosting service.
    - Personally, I used [PythonEverywhere]([url](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/)) for hosting this project.
   
## Usage
- Log in as a superuser.
- Use 'Edit words and sentences' to add topics, words and sentences.
- Use 'Import words and sentences' to import topics, words, sentences and their audio files in bulk.
- Use the home page to view words/sentences and listen to the audio that you have uploaded.
- Click 'Start quiz' to generate a random quiz using a variety of different question types.
- Use Django admin to manage user accounts.
  - All users can view data and play quizes.
  - Staff users can create, update, delete, export and import data.
  - Superuser users can access Django admin, and thus create other user accounts.
  
