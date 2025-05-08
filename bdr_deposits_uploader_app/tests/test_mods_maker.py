import datetime
import logging

from bs4 import BeautifulSoup
from django.test import SimpleTestCase

from bdr_deposits_uploader_app.lib.mods_handler import ModsMaker
from bdr_deposits_uploader_app.models import Submission

log = logging.getLogger(__name__)


class ModsMakerBasicStaticFieldsTest(SimpleTestCase):
    """
    Tests the mods_maker function with minimal submitted info.

    To add a test:
    - create a submission-instance
    - pass it to ModsMaker(submission).prepare_mods()
    - assert the expected output.
    """

    def setUp(self):
        """
        Set up the test case.
        """
        self.submission = Submission(
            title='foo foo',
            abstract='bar bar',
            created_at=datetime.datetime(2025, 5, 6, 18, 26, 37),
        )
        self.result: str = ModsMaker(self.submission).prepare_mods()
        log.debug(f'mods_maker result: ``{self.result}``')

    def test_assert_standard_mods_elements(self):
        """
        Not a direct-test; called from different test functions.
        Asserts common MODS elements that should be present in all MODS XML outputs.
        """
        self.assertIn('<mods:typeOfResource authority="primo">text_resources</mods:typeOfResource>', self.result)
        self.assertIn(
            '<mods:genre authority="aat" valueURI="http://vocab.getty.edu/aat/300444670">scholarly works</mods:genre>',
            self.result,
        )
        ## originInfo -----------------------------------------------
        self.assertIn('<mods:originInfo>', self.result)
        self.assertIn(
            '<mods:placeTerm type="code" authority="marccountry" authorityURI="http://www.loc.gov/marc/countries/">riu</mods:placeTerm>',
            self.result,
        )
        self.assertIn(
            '<mods:placeTerm type="text">Providence, Rhode Island</mods:placeTerm>',
            self.result,
        )
        self.assertIn(
            '<mods:publisher authority="naf" authorityURI="http://id.loc.gov/authorities/names">Brown University Library</mods:publisher>',
            self.result,
        )
        ## physicalDescription ---------------------------------------
        self.assertIn('<mods:physicalDescription>', self.result)
        self.assertIn('<mods:extent>1 document</mods:extent>', self.result)
        self.assertIn('<mods:digitalOrigin>born digital</mods:digitalOrigin>', self.result)
        ## accessCondition -------------------------------------------
        self.assertIn(
            '<mods:accessCondition type="use and reproduction">All rights reserved</mods:accessCondition>', self.result
        )
        self.assertIn(
            '<mods:accessCondition type="rights statement" xlink:href="http://rightsstatements.org/vocab/InC/1.0/">In Copyright</mods:accessCondition>',
            self.result,
        )
        self.assertIn(
            '<mods:accessCondition type="restriction on access">All Rights Reserved</mods:accessCondition>', self.result
        )

    ## end class ModsMakerBasicStaticFieldsTest()


class ModsMakerBasicCustomFieldsTest(SimpleTestCase):
    """
    Tests the mods_maker function with minimal submitted info.

    To add a test:
    - create a submission-instance
    - pass it to ModsMaker(submission).prepare_mods()
    - assert the expected output.
    """

    def setUp(self):
        """
        Set up the test case.
        """
        self.submission = Submission(
            title='foo foo',
            abstract='bar bar',
            created_at=datetime.datetime(2025, 5, 6, 18, 26, 37),
        )
        self.result: str = ModsMaker(self.submission).prepare_mods()
        log.debug(f'mods_maker result: ``{self.result}``')

    def test_prepare_mods_basic(self):
        """
        Tests the mods_maker function with minimal submitted info.

        This test mostly confirms the test-structure is valid.

        TODO: This submission-object would never be passed to the mods because it's missing required fields.
              Revise to use a valid minimal-info submission-object.
        """
        self.assertIn('<mods:title>foo foo</mods:title>', self.result)
        self.assertIn('<mods:abstract>bar bar</mods:abstract>', self.result)
        self.assertIn('<mods:dateCreated keyDate="yes" encoding="w3cdtf">2025</mods:dateCreated>', self.result)
        self.assertIn('<mods:dateIssued encoding="w3cdtf">2025-05-06</mods:dateIssued>', self.result)

    ## end class ModsMakerBasicCustomFieldsTest()


class ModsMakerFullTest(SimpleTestCase):
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
        self.submission = Submission(
            title='2025-may-08 7:50am title',
            abstract='abstract',
            authors='auth1first auth1last | auth2first auth2last',
            advisors_and_readers='adv-rdr1first adv-rdr1last | adv-rdr2first adv-rdr2last',
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
        self.result: str = ModsMaker(self.submission).prepare_mods()
        log.debug(f'mods_maker result: ``{self.result}``')

    def test_prepare_mods_with_full_submission(self):
        """
        Tests the mods_maker function with a submission containing all fields.
        """
        self.assertIn('<mods:title>2025-may-08 7:50am title</mods:title>', self.result)

        ## Verify fields using BeautifulSoup ------------------------
        soup = BeautifulSoup(self.result, 'xml')
        log.debug(f'soup: ``{soup}``')

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
        ## Verify that both authors have the correct namePart content
        author1_name = author_names[0].find('namePart')
        author2_name = author_names[1].find('namePart')
        self.assertIsNotNone(author1_name, 'First author should have a namePart element')
        self.assertIsNotNone(author2_name, 'Second author should have a namePart element')
        self.assertEqual(author1_name.text, 'auth1first auth1last', 'First author name should match expected text')
        self.assertEqual(author2_name.text, 'auth2first auth2last', 'Second author name should match expected text')

        ## advisors/readers check -----------------------------------
        """
        I want to check for...
        ```xml
        <mods:name type="personal">
            <mods:namePart>adv-rdr1first adv-rdr1last</mods:namePart>
            <mods:role>
                <mods:roleTerm>Advisor/Reader</mods:roleTerm>   
            </mods:role>
        </mods:name>
        <mods:name type="personal">
            <mods:namePart>adv-rdr2first adv-rdr2last</mods:namePart>
            <mods:role>
                <mods:roleTerm>Advisor/Reader</mods:roleTerm>
            </mods:role>
        </mods:name>
        ```
        """
        ## Find all name elements with advisor/reader role
        advisor_reader_names = []
        for name in name_elements:
            role_term = name.find('roleTerm', text='Advisor/Reader')
            if role_term:
                advisor_reader_names.append(name)
        log.debug(f'advisor_reader_names: ``{advisor_reader_names}``')
        self.assertEqual(len(advisor_reader_names), 2, 'Should have found 2 advisor/reader name elements')
        ## Verify each advisor/reader name has the correct role structure
        for advisor_reader_name in advisor_reader_names:
            role = advisor_reader_name.find('role')
            self.assertIsNotNone(role, 'Advisor/Reader name should have a role element')
            role_term = role.find('roleTerm')
            self.assertIsNotNone(role_term, 'Role should have a roleTerm element')
            self.assertEqual(role_term.text, 'Advisor/Reader', "Role term text should be 'Advisor/Reader'")
        ## Verify that each advisor/reader has the correct namePart content
        advisor_reader1_name = advisor_reader_names[0].find('namePart')
        advisor_reader2_name = advisor_reader_names[1].find('namePart')
        self.assertIsNotNone(advisor_reader1_name, 'First advisor-reader should have a namePart element')
        self.assertIsNotNone(advisor_reader2_name, 'Second advisor-reader should have a namePart element')
        self.assertEqual(
            advisor_reader1_name.text, 'adv-rdr1first adv-rdr1last', 'First advisor-reader name should match expected text'
        )
        self.assertEqual(
            advisor_reader2_name.text, 'adv-rdr2first adv-rdr2last', 'Second advisor-reader name should match expected text'
        )

        ## concentration check --------------------------------------
        """
        I want to check for...
        ```xml
        <mods:note displayLabel="Scholarly concentration">conc name1</mods:note>
        <mods:note displayLabel="Scholarly concentration">conc name2</mods:note>        
        ```
        """
        ## Find all note elements with concentration displayLabel
        concentration_notes = soup.find_all('note', {'displayLabel': 'Scholarly concentration'})
        self.assertEqual(len(concentration_notes), 2, 'Should have found 2 concentration note elements')
        ## Verify each concentration note has the correct content
        concentration1_note = concentration_notes[0].find('note')
        concentration2_note = concentration_notes[1].find('note')
        self.assertEqual(concentration1_note.text, 'conc name1', 'First concentration note should match expected text')
        self.assertEqual(concentration2_note.text, 'conc name2', 'Second concentration note should match expected text')

    ## end class ModsMakerFullTest()
