import datetime
import logging

from bs4 import BeautifulSoup
from django.test import SimpleTestCase

from bdr_deposits_uploader_app.lib.mods_handler import ModsMaker
from bdr_deposits_uploader_app.models import Submission

log = logging.getLogger(__name__)


class ModsMakerTest(SimpleTestCase):
    """
    Tests the mods_maker function.

    To add a test:
    - create a submission-instance
    - pass it to ModsMaker(submission).prepare_mods()
    - assert the expected output.
    """

    def setUp(self):
        """
        Set up the test case.
        """
        pass

    def assert_standard_mods_elements(self, result: str):
        """
        Not a direct-test; called from different test functions.
        Asserts common MODS elements that should be present in all MODS XML outputs.
        """
        self.assertIn('<mods:typeOfResource authority="primo">text_resources</mods:typeOfResource>', result)
        self.assertIn(
            '<mods:genre authority="aat" valueURI="http://vocab.getty.edu/aat/300444670">scholarly works</mods:genre>',
            result,
        )
        ## originInfo -----------------------------------------------
        self.assertIn('<mods:originInfo>', result)
        self.assertIn(
            '<mods:placeTerm type="code" authority="marccountry" authorityURI="http://www.loc.gov/marc/countries/">riu</mods:placeTerm>',
            result,
        )
        self.assertIn(
            '<mods:placeTerm type="text">Providence, Rhode Island</mods:placeTerm>',
            result,
        )
        self.assertIn(
            '<mods:publisher authority="naf" authorityURI="http://id.loc.gov/authorities/names">Brown University Library</mods:publisher>',
            result,
        )
        ## physicalDescription ---------------------------------------
        self.assertIn('<mods:physicalDescription>', result)
        self.assertIn('<mods:extent>1 document</mods:extent>', result)
        self.assertIn('<mods:digitalOrigin>born digital</mods:digitalOrigin>', result)
        ## accessCondition -------------------------------------------
        self.assertIn('<mods:accessCondition type="use and reproduction">All rights reserved</mods:accessCondition>', result)
        self.assertIn(
            '<mods:accessCondition type="rights statement" xlink:href="http://rightsstatements.org/vocab/InC/1.0/">In Copyright</mods:accessCondition>',
            result,
        )
        self.assertIn(
            '<mods:accessCondition type="restriction on access">All Rights Reserved</mods:accessCondition>', result
        )

    def test_prepare_mods_A(self):
        """
        Tests the mods_maker function with minimal submitted info.

        This test mostly confirms the test-structure is valid.

        TODO: This submission-object would never be passed to the mods because it's missing required fields.
              Revise to use a valid minimal-info submission-object.
        """
        submission = Submission(
            title='foo foo',
            abstract='bar bar',
            created_at=datetime.datetime(2025, 5, 6, 18, 26, 37),
        )
        result: str = ModsMaker(submission).prepare_mods()
        log.debug(f'mods_maker result: ``{result}``')
        self.assertIn('<mods:title>foo foo</mods:title>', result)
        self.assertIn('<mods:abstract>bar bar</mods:abstract>', result)
        self.assertIn('<mods:dateCreated keyDate="yes" encoding="w3cdtf">2025</mods:dateCreated>', result)
        self.assertIn('<mods:dateIssued encoding="w3cdtf">2025-05-06</mods:dateIssued>', result)
        self.assert_standard_mods_elements(result)

    def test_prepare_mods_with_full_submission(self):
        """
        Tests the mods_maker function with a submission containing all fields.
        """
        submission = Submission(
            title='2025-may-08 7:50am title',
            abstract='abstract',
            authors='auth1first auth1last | auth2first auth2last',
            advisors_and_readers='advisor reader1 | advisor reader2',
            concentrations='conc name1 | conc name2',
            degrees='degree name1 | degree name2',
            department='dept name1 | dept name2',
            faculty_mentors='faculty mentor1 | faculty mentor2',
            license_options='CC0',
            original_file_name='HH018977_0030.pdf',
            research_program='research program1 | research program2',
            team_members='team member1 | team member2',
            visibility_options='public',
            created_at=datetime.datetime(2025, 5, 8, 7, 53, 21, 29655),
        )
        result: str = ModsMaker(submission).prepare_mods()
        log.debug(f'mods_maker result: ``{result}``')
        self.assertIn('<mods:title>2025-may-08 7:50am title</mods:title>', result)

        ## author check ---------------------------------------------
        """
        I want to check for...
        ```xml
        <mods:name type="personal">
            <mods:namePart>auth1first auth1last</mods:namePart>
            <mods:role>
                <mods:roleTerm authority="marcrelator" authorityURI="http://id.loc.gov/vocabulary/relators" valueURI="http://id.loc.gov/vocabulary/relators/aut">Author</mods:roleTerm>
            </mods:role>
        </mods:name>
        <mods:name type="personal">
            <mods:namePart>auth2first auth2last</mods:namePart>
            <mods:role>
                <mods:roleTerm authority="marcrelator" authorityURI="http://id.loc.gov/vocabulary/relators" valueURI="http://id.loc.gov/vocabulary/relators/aut">Author</mods:roleTerm>
            </mods:role>
        </mods:name>
        ```
        """
        ## Verify author role structure using BeautifulSoup
        soup = BeautifulSoup(result, 'xml')
        log.debug(f'soup: ``{soup}``')
        ## Find all name elements with author role
        name_elements = soup.find_all('name')
        author_names = []
        for name in name_elements:
            role_term = name.find(
                'roleTerm', {'authority': 'marcrelator', 'valueURI': 'http://id.loc.gov/vocabulary/relators/aut'}
            )
            if role_term:
                author_names.append(name)
        log.debug(f'author_names: ``{author_names}``')
        self.assertEqual(len(author_names), 2, 'Should have found 2 author name elements')
        ## Verify each author name has the correct role structure
        for author_name in author_names:
            role = author_name.find('role')
            self.assertIsNotNone(role, 'Author name should have a role element')
            role_term = role.find('roleTerm')
            self.assertIsNotNone(role_term, 'Role should have a roleTerm element')
            self.assertEqual(role_term.text, 'Author', "Role term text should be 'Author'")
            self.assertEqual(role_term['authority'], 'marcrelator', 'Role term should have correct authority')
            self.assertEqual(
                role_term['valueURI'],
                'http://id.loc.gov/vocabulary/relators/aut',
                'Role term should have correct valueURI',
            )
        ## Verify that both authors are present in the text content
        self.assertIn('auth1first auth1last', result)
        self.assertIn('auth2first auth2last', result)
        ## check standard MODS elements -----------------------------
        self.assert_standard_mods_elements(result)
