"""
Seed realistic demo teachers across many fields (not just tech) so Discover and
the dashboard look alive. Idempotent: running it again updates the same accounts
rather than creating duplicates. Pass --fresh to remove previously seeded demo
users first.

    python manage.py seed_demo
    python manage.py seed_demo --fresh
"""
import random

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from editor.models import Skill, UserProfile

# Every seeded account carries this flag in its first_name-independent way via a
# known email domain, so --fresh can find and remove exactly these and nothing else.
DEMO_DOMAIN = "demo.skillbridge.local"
DEMO_PASSWORD = "skillbridge123"

# (username, full name, avatar, college, department, bio,
#  [ (teach skill, category, proficiency) ... ], learn_skills, avg_rating, rating_count)
PEOPLE = [
    ("priya_nair", "Priya Nair", "w1.jpg", "KM Music Conservatory", "Hindustani Classical",
     "Trained vocalist teaching ragas, breath control, and sight-singing. Patient with absolute beginners.",
     [("Hindustani Vocals", "Music", "Advanced"), ("Music Theory", "Music", "Intermediate")],
     "Piano, Songwriting", 4.9, 27),
    ("marcus_bennett", "Marcus Bennett", "c1.jpg", "Berklee Online", "Guitar Performance",
     "Gigging guitarist. I teach chords, fingerstyle, and how to actually jam with other people.",
     [("Acoustic Guitar", "Music", "Advanced"), ("Music Production", "Music", "Intermediate")],
     "Mixing, Spanish", 4.7, 41),
    ("sofia_romero", "Sofia Romero", "w2.jpg", "Universidad de Salamanca", "Linguistics",
     "Native Spanish speaker from Seville. Conversation-first lessons, no boring grammar drills.",
     [("Spanish Conversation", "Languages", "Advanced"), ("Latin American Culture", "Languages", "Intermediate")],
     "Portuguese, Watercolor", 4.8, 33),
    ("kenji_tanaka", "Kenji Tanaka", "c2.jpg", "Waseda University", "Japanese Studies",
     "JLPT-focused Japanese tutor. We build from hiragana up to real reading and listening.",
     [("Japanese (JLPT N5-N3)", "Languages", "Advanced"), ("Kanji Memory Techniques", "Languages", "Advanced")],
     "Public Speaking", 4.6, 19),
    ("aisha_khan", "Aisha Khan", "w1.jpg", "National College of Arts", "Fine Arts",
     "Watercolor and gouache artist. I'll get you from blank page to a finished loose landscape.",
     [("Watercolor Painting", "Design", "Advanced"), ("Color Theory", "Design", "Intermediate")],
     "Digital Art, French", 5.0, 12),
    ("liam_oconnor", "Liam O'Connor", "c3.jpg", "Trinity College Dublin", "Mathematics",
     "Chess coach (ECF 2050). We study your own games and fix the habits losing you points.",
     [("Chess Strategy", "Academics", "Advanced"), ("Endgame Technique", "Academics", "Intermediate")],
     "Guitar", 4.9, 48),
    ("nadia_hassan", "Nadia Hassan", "w2.jpg", "Cairo University", "Physics",
     "Physics and calculus tutor. Great at making limits, derivatives, and mechanics finally click.",
     [("Calculus", "Academics", "Advanced"), ("High School Physics", "Academics", "Advanced")],
     "Data Analysis", 4.8, 36),
    ("chen_wei", "Chen Wei", "c4.jpg", "Peking University", "Chinese Language",
     "Mandarin teacher focusing on tones and everyday speaking. Pinyin to short conversations.",
     [("Mandarin Chinese", "Languages", "Advanced"), ("Chinese Calligraphy", "Design", "Intermediate")],
     "UX Design", 4.7, 22),
    ("isabella_rossi", "Isabella Rossi", "w1.jpg", "Università di Bologna", "Culinary Arts",
     "Home cook from Bologna. Fresh pasta, ragù, and simple weeknight Italian you'll actually make.",
     [("Italian Home Cooking", "Other", "Advanced"), ("Pasta from Scratch", "Other", "Advanced")],
     "Food Photography", 5.0, 15),
    ("diego_fernandez", "Diego Fernandez", "c5.jpg", "Instituto de Danza", "Dance",
     "Salsa and bachata instructor. Lead or follow, we start with timing and confidence.",
     [("Salsa Dancing", "Other", "Advanced"), ("Bachata Basics", "Other", "Intermediate")],
     "Video Editing", 4.6, 29),
    ("grace_thompson", "Grace Thompson", "w2.jpg", "London School of Economics", "Communications",
     "Ex-debate champion. I coach public speaking, pitch decks, and beating stage fright.",
     [("Public Speaking", "Business", "Advanced"), ("Presentation Design", "Business", "Intermediate")],
     "Spanish, Photography", 4.9, 31),
    ("omar_farouk", "Omar Farouk", "c6.jpg", "INSEAD", "Finance",
     "Help students with budgeting, saving, and the basics of investing. Plain English, no jargon.",
     [("Personal Finance", "Business", "Advanced"), ("Intro to Investing", "Business", "Intermediate")],
     "Excel, Mandarin", 4.8, 24),
    ("hannah_schmidt", "Hannah Schmidt", "w1.jpg", "Yoga Alliance RYT-500", "Wellness",
     "Certified yoga teacher. Gentle vinyasa, breathwork, and a short daily mobility routine.",
     [("Yoga & Mindfulness", "Other", "Advanced"), ("Meditation Basics", "Other", "Intermediate")],
     "German, Journaling", 4.9, 38),
    ("ravi_patel", "Ravi Patel", "c1.jpg", "NID Ahmedabad", "Photography",
     "Street and portrait photographer. We cover exposure, composition, and editing in Lightroom.",
     [("Photography", "Design", "Advanced"), ("Lightroom Editing", "Design", "Intermediate")],
     "Public Speaking", 4.7, 26),
    ("emma_wilson", "Emma Wilson", "w2.jpg", "University of Iowa", "Creative Writing",
     "Fiction writer and editor. Short stories, character, and getting past the blank page.",
     [("Creative Writing", "Academics", "Advanced"), ("Editing & Proofreading", "Academics", "Intermediate")],
     "Italian, Watercolor", 4.8, 20),
    ("yuki_sato", "Yuki Sato", "c2.jpg", "Tama Art University", "Illustration",
     "Freelance illustrator. Procreate from first sketch to finished character art.",
     [("Digital Illustration", "Design", "Advanced"), ("Procreate for Beginners", "Design", "Intermediate")],
     "Japanese, Animation", 5.0, 17),
]


class Command(BaseCommand):
    help = "Create realistic demo teacher profiles across many fields."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="Delete previously seeded demo users before creating them again.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["fresh"]:
            qs = User.objects.filter(email__endswith="@" + DEMO_DOMAIN)
            count = qs.count()
            qs.delete()
            self.stdout.write(self.style.WARNING(f"Removed {count} existing demo user(s)."))

        created, updated = 0, 0
        for (username, full_name, avatar, college, dept, bio,
             teach_skills, learn_skills, avg_rating, rating_count) in PEOPLE:
            user, is_new = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@{DEMO_DOMAIN}"},
            )
            first, _, last = full_name.partition(" ")
            user.first_name = first
            user.last_name = last
            user.email = f"{username}@{DEMO_DOMAIN}"
            user.set_password(DEMO_PASSWORD)
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.credits = random.randint(6, 24)
            profile.college = college
            profile.department = dept
            profile.bio = bio
            profile.avatar = avatar
            profile.learn_skills = learn_skills
            profile.available_hours = random.choice(
                ["3 hrs / week", "5 hrs / week", "8 hrs / week", "10 hrs / week"]
            )
            profile.schedule = random.choice(
                ["Weekday evenings", "Weekends", "Weekday mornings", "Flexible"]
            )
            profile.is_public = True
            profile.show_hours = True
            profile.allow_requests = True
            profile.average_rating = avg_rating
            profile.rating_count = rating_count
            profile.save()

            # Reset this account's teach skills so re-running stays clean.
            Skill.objects.filter(user=user, skill_type="TEACH").delete()
            for name, category, proficiency in teach_skills:
                Skill.objects.create(
                    user=user,
                    name=name,
                    category=category,
                    skill_type="TEACH",
                    proficiency=proficiency,
                    rating=avg_rating,
                )

            created += 1 if is_new else 0
            updated += 0 if is_new else 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(PEOPLE)} demo teachers ({created} new, {updated} updated)."
        ))
        self.stdout.write(f"All demo accounts use the password: {DEMO_PASSWORD}")
