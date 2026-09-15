from __future__ import annotations

from unittest import mock

from django.test import SimpleTestCase, override_settings

from bdr_uploader_hub_app.forms.staff_form import StaffForm
from bdr_uploader_hub_app.lib.ingester_handler import Ingester
from bdr_uploader_hub_app.lib.object_type_helper import (
    DEFAULT_OBJECT_TYPE_ENTRY,
    build_object_type_choices,
    get_object_type_entry,
)

OBJECT_TYPE_OPTIONS: list[dict] = [
    {
        'menu_label': 'none',
        'uri': '',
    },
    {
        'menu_label': 'bachelors thesis',
        'uri': 'http://purl.org/spar/fabio/BachelorsThesis',
    },
    {
        'menu_label': 'masters thesis',
        'uri': 'http://purl.org/spar/fabio/MastersThesis',
    },
    {
        'menu_label': 'doctoral thesis',
        'uri': 'http://purl.org/spar/fabio/DoctoralThesis',
    },
]


class ObjectTypeHelperTest(SimpleTestCase):
    """
    Checks object type helper behavior.
    """

    @override_settings(OBJECT_TYPE_OPTIONS=OBJECT_TYPE_OPTIONS)
    def test_helper_normalizes_choices_and_defaults_missing_selection_to_none(self):
        """
        Checks helper choice-building and missing-selection normalization.
        """
        self.assertEqual(
            [
                ('bachelors thesis', 'bachelors thesis'),
                ('doctoral thesis', 'doctoral thesis'),
                ('masters thesis', 'masters thesis'),
                ('none', 'none'),
            ],
            build_object_type_choices(),
        )
        self.assertEqual(OBJECT_TYPE_OPTIONS[0], get_object_type_entry(None))
        self.assertEqual(OBJECT_TYPE_OPTIONS[0], get_object_type_entry(''))
        self.assertEqual(OBJECT_TYPE_OPTIONS[0], get_object_type_entry({'menu_label': ''}))

    @override_settings(OBJECT_TYPE_OPTIONS=OBJECT_TYPE_OPTIONS)
    def test_get_object_type_entry_raises_for_unknown_menu_label(self):
        """
        Checks unknown object type labels raise ValueError.
        """
        with self.assertRaisesRegex(ValueError, 'Unknown object type menu_label: invalid'):
            get_object_type_entry('invalid')

    @override_settings(
        OBJECT_TYPE_OPTIONS=[
            {
                'menu_label': 'masters thesis',
                'uri': 'http://purl.org/spar/fabio/MastersThesis',
            }
        ]
    )
    def test_helper_adds_builtin_none_entry_when_settings_omit_it(self):
        """
        Checks helper falls back to a built-in none entry when settings omit it.
        """
        self.assertEqual(
            [
                ('masters thesis', 'masters thesis'),
                ('none', 'none'),
            ],
            build_object_type_choices(),
        )
        self.assertEqual(DEFAULT_OBJECT_TYPE_ENTRY, get_object_type_entry(None))


class StaffFormObjectTypeTest(SimpleTestCase):
    """
    Checks staff form object type behavior.
    """

    @override_settings(
        OBJECT_TYPE_OPTIONS=OBJECT_TYPE_OPTIONS,
        ALL_LICENSE_OPTIONS=[('CC_BY', 'CC BY')],
        ALL_VISIBILITY_OPTIONS=[('public', 'Public')],
    )
    def test_assigned_object_type_field_choices_and_default(self):
        """
        Checks assigned object type field choices and default value.
        """
        form = StaffForm()

        self.assertEqual(
            [
                ('bachelors thesis', 'bachelors thesis'),
                ('doctoral thesis', 'doctoral thesis'),
                ('masters thesis', 'masters thesis'),
                ('none', 'none'),
            ],
            list(form.fields['assigned_object_type'].choices),
        )
        self.assertEqual('none', form.fields['assigned_object_type'].initial)
        self.assertEqual('none', form.initial['assigned_object_type'])
        self.assertEqual('none', form['assigned_object_type'].value())


class IngesterObjectTypeTest(SimpleTestCase):
    """
    Checks ingest object type rels behavior.
    """

    @override_settings(OBJECT_TYPE_OPTIONS=OBJECT_TYPE_OPTIONS)
    def test_prepare_rels_adds_type_when_object_type_selected(self):
        """
        Checks ingest rels include rdf:type when object type has a uri.
        """
        submission = mock.Mock()
        submission.target_collection_pid = 'test:submission'

        rels = Ingester().prepare_rels(
            submission,
            {
                'collection_pid': 'test:app',
                'assigned_object_type': {
                    'menu_label': 'masters thesis',
                    'uri': 'http://purl.org/spar/fabio/MastersThesis',
                },
            },
        )

        self.assertEqual(
            {
                'isMemberOfCollection': 'test:submission',
                'type': 'http://purl.org/spar/fabio/MastersThesis',
            },
            rels,
        )

    @override_settings(OBJECT_TYPE_OPTIONS=OBJECT_TYPE_OPTIONS)
    def test_prepare_rels_omits_type_when_object_type_is_none(self):
        """
        Checks ingest rels omit rdf:type when the none option is selected.
        """
        submission = mock.Mock()
        submission.target_collection_pid = None

        rels = Ingester().prepare_rels(
            submission,
            {
                'collection_pid': 'test:app',
                'assigned_object_type': {
                    'menu_label': 'none',
                    'uri': '',
                },
            },
        )

        self.assertEqual({'isMemberOfCollection': 'test:app'}, rels)

    @override_settings(OBJECT_TYPE_OPTIONS=OBJECT_TYPE_OPTIONS)
    def test_prepare_rels_legacy_config_without_object_type_matches_current_payload(self):
        """
        Checks legacy app config without object type keeps the existing rels payload.
        """
        submission = mock.Mock()
        submission.target_collection_pid = None

        rels = Ingester().prepare_rels(submission, {'collection_pid': 'test:app'})

        self.assertEqual({'isMemberOfCollection': 'test:app'}, rels)
