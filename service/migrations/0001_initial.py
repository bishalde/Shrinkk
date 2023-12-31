# Generated by Django 3.2.19 on 2023-07-03 05:16

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='subscriberInformation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=150, unique=True)),
                ('dateTime', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='URLInformation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('original_url', models.URLField()),
                ('short_code', models.CharField(max_length=10, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='URLSClicked',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.PositiveBigIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='URLSMade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.PositiveBigIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='userInformation',
            fields=[
                ('username', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=150, unique=True)),
                ('password', models.CharField(max_length=50)),
                ('createdDate', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
