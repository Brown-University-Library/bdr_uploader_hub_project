import datetime
import logging

from django.test import SimpleTestCase

from bdr_deposits_uploader_app.lib.mods_handler import ModsMaker
from bdr_deposits_uploader_app.models import Submission

log = logging.getLogger(__name__)


class ModsMakerTest(SimpleTestCase):
    """
    Tests the mods_maker function.
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
