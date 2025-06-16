import datetime
import logging

from bs4 import BeautifulSoup
from django.test import SimpleTestCase

from bdr_student_uploader_hub_app.lib.mods_handler import ModsMaker
from bdr_student_uploader_hub_app.models import Submission

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
        self.mods_maker = ModsMaker(self.submission)
        self.result: str = self.mods_maker.prepare_mods()
        log.debug(f'mods_maker result: ``{self.result}``')

    def test_assert_standard_mods_elements(self):
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
        self.mods_maker = ModsMaker(self.submission)
        self.result: str = self.mods_maker.prepare_mods()
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
    Tests the mods_maker function by submitting a full submission-object with fields containing multiple values.
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
            department='Biology, Brown University | Molecular Biology',
            faculty_mentors='faculty mentor1 | faculty mentor2',
            license_options='CC0',
            original_file_name='HH018977_0030.pdf',
            research_program='research program1 | research program2',
            team_members='team member1 | team member2',
            visibility_options='public',
            created_at=datetime.datetime(2025, 5, 8, 7, 53, 21, 29655),
        )
        self.mods_maker = ModsMaker(self.submission)
        self.result: str = self.mods_maker.prepare_mods()
        self.soup = BeautifulSoup(self.result, 'xml')
        log.debug(f'mods_maker result: ``{self.result}``')

    def test_validate_xml_with_valid_xml(self):
        """
        Tests that the validate_xml function returns True when the XML is well-formed.
        Doesn't validate MODS specifcally (will).
        """
        xml_str = """<mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
<titleInfo><title>Test Title</title></titleInfo>
<typeOfResource>text</typeOfResource></mods:mods>"""
        valid: bool = self.mods_maker.validate_xml(xml_str)
        self.assertEqual(valid, True)

    def test_validate_xml_with_invalid_xml(self):
        """
        Tests that the validate_xml function returns False when the XML is not well-formed.
        """
        xml_str = '<mods:mods>'
        valid: bool = self.mods_maker.validate_xml(xml_str)
        self.assertEqual(valid, False)

    def test_format_xml(self):
        """
        Tests that the format_xml function properly formats XML with proper indentation and line breaks.
        """
        ## create a sample XML string with minimal formatting
        xml_str = """<mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
<titleInfo><title>Test Title</title></titleInfo>
<typeOfResource>text</typeOfResource></mods:mods>"""
        ## expected formatted output
        expected_formatted = """<mods:mods xmlns:mods="http://www.loc.gov/mods/v3">
  <titleInfo>
    <title>Test Title</title>
  </titleInfo>
  <typeOfResource>text</typeOfResource>
</mods:mods>
"""
        ## format and test
        formatted_xml = self.mods_maker.format_xml(xml_str)
        self.assertEqual(formatted_xml.strip(), expected_formatted.strip())

    def test_title_generation(self):
        """
        Tests that the title is correctly generated in the MODS XML.
        """
        self.assertIn('<mods:title>2025-may-08 7:50am title</mods:title>', self.result)

    def test_author_generation(self):
        """
        Tests that authors are correctly generated with proper role attributes.

        Expected XML structure:
        ```xml
        <mods:name type="personal">
            <mods:namePart>auth1first auth1last</mods:namePart>
            <mods:role>
                <mods:roleTerm authority="marcrelator" authorityURI="http://id.loc.gov/vocabulary/relators" valueURI="http://id.loc.gov/vocabulary/relators/aut">Author</mods:roleTerm>
            </mods:role>
        </mods:name>
        ```
        """
        name_elements = self.soup.find_all('name')
        author_names = []
        for name in name_elements:
            role_term = name.find(
                'roleTerm', {'authority': 'marcrelator', 'valueURI': 'http://id.loc.gov/vocabulary/relators/aut'}
            )
            if role_term:
                author_names.append(name)
        self.assertEqual(len(author_names), 2, 'Should have found 2 author name elements')

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

        author1_name = author_names[0].find('namePart')
        author2_name = author_names[1].find('namePart')
        self.assertIsNotNone(author1_name, 'First author should have a namePart element')
        self.assertIsNotNone(author2_name, 'Second author should have a namePart element')
        self.assertEqual(author1_name.text, 'auth1first auth1last', 'First author name should match expected text')
        self.assertEqual(author2_name.text, 'auth2first auth2last', 'Second author name should match expected text')
        ## end def test_author_generation()

    def test_advisor_reader_generation(self):
        """
        Tests that advisors and readers are correctly generated with proper role attributes.

        Expected XML structure:
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
        name_elements = self.soup.find_all('name')
        advisor_reader_names = []
        for name in name_elements:
            role_term = name.find('roleTerm', text='Advisor/Reader')
            if role_term:
                advisor_reader_names.append(name)
        self.assertEqual(len(advisor_reader_names), 2, 'Should have found 2 advisor/reader name elements')

        for advisor_reader_name in advisor_reader_names:
            role = advisor_reader_name.find('role')
            self.assertIsNotNone(role, 'Advisor/Reader name should have a role element')
            role_term = role.find('roleTerm')
            self.assertIsNotNone(role_term, 'Role should have a roleTerm element')
            self.assertEqual(role_term.text, 'Advisor/Reader', "Role term text should be 'Advisor/Reader'")

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

        ## end def test_advisor_reader_generation()

    def test_concentration_generation(self):
        """
        Tests that concentrations are correctly generated as notes with proper displayLabel.

        Expected XML structure:
        ```xml
        <mods:note type="fieldOfStudy" displayLabel="Scholarly concentration">conc name1</mods:note>
        <mods:note type="fieldOfStudy" displayLabel="Scholarly concentration">conc name2</mods:note>
        ```
        """
        concentration_notes = self.soup.find_all('note', {'type': 'fieldOfStudy', 'displayLabel': 'Scholarly concentration'})
        self.assertEqual(len(concentration_notes), 2, 'Should have found 2 concentration note elements')

        ## verify each concentration note has the correct content
        concentration1_note = concentration_notes[0]
        concentration2_note = concentration_notes[1]
        self.assertEqual(concentration1_note.text, 'conc name1', 'First concentration note should match expected text')
        self.assertEqual(concentration2_note.text, 'conc name2', 'Second concentration note should match expected text')

    def test_degree_generation(self):
        """
        Tests that degrees are correctly generated as notes with proper displayLabel.

        Expected XML structure:
        ```xml
        <mods:note type="degree" displayLabel="Degree">degree name1</mods:note>
        <mods:note type="degree" displayLabel="Degree">degree name2</mods:note>
        ```
        """
        degree_notes = self.soup.find_all('note', {'type': 'degree', 'displayLabel': 'Degree'})
        self.assertEqual(len(degree_notes), 2, 'Should have found 2 degree note elements')

        ## verify each degree note has the correct content
        degree1_note = degree_notes[0]
        degree2_note = degree_notes[1]
        self.assertEqual(degree1_note.text, 'degree name1', 'First degree note should match expected text')
        self.assertEqual(degree2_note.text, 'degree name2', 'Second degree note should match expected text')

    def test_department_generation(self):
        """
        Tests that departments are correctly generated as corporate names with proper role attributes.

        Expected XML structure:
        ```xml
        <mods:name type="corporate">
            <mods:namePart>Biology, Brown University</mods:namePart>
            <mods:role>
                <mods:roleTerm
                authority="marcrelator"
                type="text"
                valueURI="http://id.loc.gov/vocabulary/relators/spn"
                >sponsor</mods:roleTerm>
            </mods:role>
        </mods:name>
        <mods:name type="corporate">
            <mods:namePart>Molecular Biology, Brown University</mods:namePart>
            <mods:role>
                <mods:roleTerm
                authority="marcrelator"
                type="text"
                valueURI="http://id.loc.gov/vocabulary/relators/spn"
                >sponsor</mods:roleTerm>
            </mods:role>
        </mods:name>
        ```
        """
        name_elements = self.soup.find_all('name')
        department_names = []
        for name in name_elements:
            if name.get('type') == 'corporate':
                role_term = name.find(
                    'roleTerm', {'authority': 'marcrelator', 'valueURI': 'http://id.loc.gov/vocabulary/relators/spn'}
                )
                if role_term and role_term.text == 'sponsor':
                    department_names.append(name)
        self.assertEqual(len(department_names), 2, 'Should have found 2 department name elements')

        for department_name in department_names:
            role = department_name.find('role')
            self.assertIsNotNone(role, 'Department name should have a role element')
            role_term = role.find('roleTerm')
            self.assertIsNotNone(role_term, 'Role should have a roleTerm element')
            self.assertEqual(role_term.text, 'sponsor', "Role term text should be 'sponsor'")
            self.assertEqual(role_term['authority'], 'marcrelator', 'Role term should have correct authority')
            self.assertEqual(
                role_term['valueURI'], 'http://id.loc.gov/vocabulary/relators/spn', 'Role term should have correct valueURI'
            )
            self.assertEqual(role_term['type'], 'text', 'Role term should have correct type')

        department1_name = department_names[0].find('namePart')
        department2_name = department_names[1].find('namePart')
        self.assertIsNotNone(department1_name, 'First department should have a namePart element')
        self.assertIsNotNone(department2_name, 'Second department should have a namePart element')
        self.assertEqual(
            department1_name.text, 'Biology, Brown University', 'First department name should match expected text'
        )
        self.assertEqual(
            department2_name.text, 'Molecular Biology, Brown University', 'Second department name should match expected text'
        )

        ## end def test_department_generation()

    def test_faculty_mentors_generation(self):
        """
        Tests that the faculty mentors are correctly generated in the MODS XML.

        Expected XML structure:
        ```xml
        <mods:name type="personal">
            <mods:namePart>faculty mentor1</mods:namePart>
            <mods:role>
                <mods:roleTerm authority="local" type="text">Faculty Mentor</mods:roleTerm>
            </mods:role>
        </mods:name>
        <mods:name type="personal">
            <mods:namePart>faculty mentor2</mods:namePart>
            <mods:role>
                <mods:roleTerm authority="local" type="text">Faculty Mentor</mods:roleTerm>
            </mods:role>
        </mods:name>
        ```
        """
        # Verify the number of faculty mentor name elements
        soup = BeautifulSoup(self.result, 'lxml-xml')
        name_elements = soup.find_all('mods:name', {'type': 'personal'})
        faculty_mentors = [
            name for name in name_elements if name.find('mods:roleTerm', text=lambda t: t and 'Faculty Mentor' in t)
        ]
        self.assertEqual(len(faculty_mentors), 2, 'Should have found 2 faculty mentor name elements')

        # Verify the first faculty mentor
        first_mentor = faculty_mentors[0]
        self.assertEqual(first_mentor.find('mods:namePart').text, 'faculty mentor1')
        self.assertEqual(first_mentor.find('mods:roleTerm').text, 'Faculty Mentor')
        self.assertEqual(first_mentor.find('mods:roleTerm')['authority'], 'local')
        self.assertEqual(first_mentor.find('mods:roleTerm')['type'], 'text')

        # Verify the second faculty mentor
        second_mentor = faculty_mentors[1]
        self.assertEqual(second_mentor.find('mods:namePart').text, 'faculty mentor2')
        self.assertEqual(second_mentor.find('mods:roleTerm').text, 'Faculty Mentor')
        self.assertEqual(second_mentor.find('mods:roleTerm')['authority'], 'local')
        self.assertEqual(second_mentor.find('mods:roleTerm')['type'], 'text')

        ## end def test_faculty_mentor_generation()

    def test_team_members_generation(self):
        """
        Tests that team members are correctly generated as personal name elements with proper role attributes.

        Expected XML structure:
        ```xml
        <mods:name type="personal">
            <mods:namePart>team1first team1last</mods:namePart>
            <mods:role>
                <mods:roleTerm authority="local" type="text">Team Member</mods:roleTerm>
            </mods:role>
        </mods:name>
        <mods:name type="personal">
            <mods:namePart>team2first team2last</mods:namePart>
            <mods:role>
                <mods:roleTerm authority="local" type="text">Team Member</mods:roleTerm>
            </mods:role>
        </mods:name>
        ```
        """
        name_elements = self.soup.find_all('name')
        team_member_names = []
        for name in name_elements:
            role_term = name.find('roleTerm', text='Team Member')
            if role_term:
                team_member_names.append(name)

        log.debug(f'Found {len(team_member_names)} team member name elements')
        log.debug(f'Actual XML: {self.result}')

        self.assertEqual(len(team_member_names), 2, 'Should have found 2 team member name elements')

        ## verify each team member has correct structure and content
        team_member1 = team_member_names[0]
        team_member2 = team_member_names[1]

        ## verify type attribute
        self.assertEqual(team_member1['type'], 'personal', 'First team member should have type="personal"')
        self.assertEqual(team_member2['type'], 'personal', 'Second team member should have type="personal"')

        ## verify namePart content
        team_member1_name = team_member1.find('namePart')
        team_member2_name = team_member2.find('namePart')
        self.assertIsNotNone(team_member1_name, 'First team member should have a namePart element')
        self.assertIsNotNone(team_member2_name, 'Second team member should have a namePart element')
        self.assertEqual(team_member1_name.text, 'team member1', 'First team member name should match expected text')
        self.assertEqual(team_member2_name.text, 'team member2', 'Second team member name should match expected text')

        ## verify roleTerm attributes and content
        team_member1_role_term = team_member1.find('roleTerm')
        team_member2_role_term = team_member2.find('roleTerm')
        self.assertIsNotNone(team_member1_role_term, 'First team member should have a roleTerm element')
        self.assertIsNotNone(team_member2_role_term, 'Second team member should have a roleTerm element')
        self.assertEqual(team_member1_role_term.text, 'Team Member', 'First team member role term should be "Team Member"')
        self.assertEqual(team_member2_role_term.text, 'Team Member', 'Second team member role term should be "Team Member"')
        self.assertEqual(
            team_member1_role_term['authority'], 'local', 'First team member role term should have authority="local"'
        )
        self.assertEqual(
            team_member2_role_term['authority'], 'local', 'Second team member role term should have authority="local"'
        )
        self.assertEqual(team_member1_role_term['type'], 'text', 'First team member role term should have type="text"')
        self.assertEqual(team_member2_role_term['type'], 'text', 'Second team member role term should have type="text"')

        ## end def test_team_members_generation()

    def test_mods_access_condition_generation(self):
        """
        Tests that the access conditions are correctly generated in the MODS XML.

        Expected XML structure:
        ```xml
        <mods:accessCondition type="use and reproduction">Creative Commons Zero (CC0) - No Rights Reserved</mods:accessCondition>
        <mods:accessCondition type="license" xlink:href="https://creativecommons.org/publicdomain/zero/1.0/">Creative Commons CC0 1.0 Universal Public Domain Dedication</mods:accessCondition>
        ```
        """
        soup = BeautifulSoup(self.result, 'lxml-xml')
        access_conditions = soup.find_all('mods:accessCondition')
        self.assertEqual(len(access_conditions), 2, 'Should have found 2 access condition elements')
        self.assertEqual(
            access_conditions[0]['type'],
            'use and reproduction',
            'First access condition should have type="use and reproduction"',
        )
        self.assertEqual(access_conditions[0].text, 'Creative Commons Zero (CC0) - No Rights Reserved')
        self.assertEqual(access_conditions[1]['type'], 'license', 'Second access condition should have type="license"')
        self.assertEqual(access_conditions[1]['xlink:href'], 'https://creativecommons.org/publicdomain/zero/1.0/')
        self.assertEqual(access_conditions[1].text, 'Creative Commons CC0 1.0 Universal Public Domain Dedication')

    ## end class ModsMakerFullTest()
