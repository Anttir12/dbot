# Generated by Django 4.1 on 2022-10-22 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sounds", "0017_permissions"),
    ]

    operations = [
        migrations.AlterField(
            model_name="oweventsoundeffect",
            name="event",
            field=models.CharField(
                choices=[
                    ("double_kill", "Double Kill"),
                    ("triple_kill", "Triple Kill"),
                    ("quadruple_kill", "Quadruple Kill"),
                    ("quintuple_kill", "Quintuple Kill"),
                    ("sextuple_kill", "Sextuple Kill"),
                    ("team_kill", "Team Kill"),
                    ("hook_kill", "Hook Kill"),
                    ("critical_hit", "Critical Hit"),
                ],
                max_length=64,
            ),
        ),
        migrations.AlterField(
            model_name="oweventsoundeffect",
            name="hero",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Ana", "Ana"),
                    ("Ashe", "Ashe"),
                    ("Baptiste", "Baptiste"),
                    ("Bastion", "Bastion"),
                    ("Brigitte", "Brigitte"),
                    ("Doomfist", "Doomfist"),
                    ("Dva", "Dva"),
                    ("Echo", "Echo"),
                    ("Genji", "Genji"),
                    ("Hanzo", "Hanzo"),
                    ("Junkerqueen", "Junkerqueen"),
                    ("Junkrat", "Junkrat"),
                    ("Lucio", "Lucio"),
                    ("Kiriko", "Kiriko"),
                    ("Mcree", "Mcree"),
                    ("Mei", "Mei"),
                    ("Mercy", "Mercy"),
                    ("Moira", "Moira"),
                    ("Orisa", "Orisa"),
                    ("Pharah", "Pharah"),
                    ("Reaper", "Reaper"),
                    ("Reinhardt", "Reinhardt"),
                    ("Roadhog", "Roadhog"),
                    ("Sigma", "Sigma"),
                    ("Soldier", "Soldier"),
                    ("Sojourn", "Sojourn"),
                    ("Sombra", "Sombra"),
                    ("Symmetra", "Symmetra"),
                    ("Torbjorn", "Torbjorn"),
                    ("Tracer", "Tracer"),
                    ("Widowmaker", "Widowmaker"),
                    ("Winston", "Winston"),
                    ("Wreckingball", "Wreckingball"),
                    ("Zarya", "Zarya"),
                    ("Zenyatta", "Zenyatta"),
                ],
                max_length=64,
                null=True,
            ),
        ),
    ]
