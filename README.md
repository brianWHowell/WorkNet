# WorkNet

A full-stack job marketplace built with Django, connecting job seekers and recruiters.

## Collaboration (first and foremost)
WorkNet was built by myself and a small team of my peers:
[kstrickland04](https://github.com/kstrickland04),
[h-tambareni](https://github.com/h-tambareni), and
[vedkaria](https://github.com/vedkaria).

We built WorkNet to practice software design, software engineering workflow, and design documentation, using Scrum over 3 sprints with a Trello board and design docs.

## Features
- Role-based accounts for job seekers, recruiters and admins
- Job listings with an admin approval and rejection flow
- Application pipeline (applied->review->interview->offer->closed)
- Job recommendations based on a seeker's skills
- Map-based job search with Leaflet and OpenStreetMap
- In-app messaging and notifications

**Tech:** Python, Django 5, SQLite, Bootstrap, Leaflet

## To Run Locally
    pip install django
    python manage.py runserver

Then view at http://127.0.0.1:8000. The admin panel is at http://127.0.0.1:8000/admin.

## Demo accounts
| Role | Username | Password |
|---|---|---|
| Admin | admin | Admin123 |
| Job seeker | seeker_demo | Seeker123 |
| Recruiter | recruiter_demo | Recruiter123 |

The seeker and recruiter accounts have sample data, so all parts of the site can be interacted with.
