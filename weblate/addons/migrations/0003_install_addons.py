# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-03 21:59
from __future__ import print_function, unicode_literals

from django.db import migrations

from weblate.trans.formats import FILE_FORMATS
from weblate.addons.models import ADDONS

HOOKS_REPLACE = {
    '/hook-update-resx': 'weblate.cleanup.generic',
    '/hook-cleanup-android': 'weblate.cleanup.generic',
    '/hook-generate-mo': 'weblate.gettext.mo',
    '/hook-sort-properties': 'weblate.properties.sort',
    '/hook-update-linguas': 'weblate.gettext.linguas',
}
HOOKS_FORMATS = {
    '/hook-unwrap-po': 'po-unwrapped',
    '/hook-json_restore_hierarchy': 'json-nested',
}
FLAGS_REPLACE = {
    'add-source-review': 'weblate.flags.source_edit',
    'add-review': 'weblate.flags.target_edit',
}

HOOKS = (
    'post_update_script',
    'pre_commit_script',
    'post_commit_script',
    'post_push_script',
    'post_add_script',
)

MESSAGE = '{}/{}: Keeping {} hook, file format {} not supported!'


def single_addon(Addon, Event, component, name):
    addon = Addon.objects.get_or_create(
        component=component,
        name=name,
    )[0]
    for event in ADDONS[name].events:
        Event.objects.get_or_create(
            addon=addon,
            event=event,
        )


def install_addons(apps, schema_editor):
    """Install addons as replacement for hooks or flags."""
    SubProject = apps.get_model('trans', 'SubProject')
    Addon = apps.get_model('addons', 'Addon')
    Event = apps.get_model('addons', 'Event')

    for component in SubProject.objects.all():
        changed = False
        for name in HOOKS:
            hook = getattr(component, name)
            for match, replacement in HOOKS_REPLACE.items():
                if hook.endswith(match):
                    setattr(component, name, '')
                    single_addon(Addon, Event, component, replacement)
                    changed = True
            for match, replacement in HOOKS_FORMATS.items():
                if hook.endswith(match):
                    if replacement in FILE_FORMATS:
                        component.file_format = replacement
                        changed = True
                    else:
                        print(MESSAGE.format(
                            component.project.slug, component.slug,
                            match, replacement,
                        ))
        for match, replacement in FLAGS_REPLACE.items():
            if match in component.check_flags:
                component.check_flags.replace(
                    match, ''
                ).replace(' ', '').replace(',,', ',')
                single_addon(Addon, Event, component, replacement)
                changed = True

        if changed:
            component.save()


class Migration(migrations.Migration):

    dependencies = [
        ('addons', '0002_auto_20180203_2258'),
    ]

    operations = [
        migrations.RunPython(install_addons),
    ]
