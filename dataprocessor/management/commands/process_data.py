import json
import logging
import uuid
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

import colorama
from dateutil import parser as date_parser
from django.core.management.base import BaseCommand
from django.utils.timezone import is_naive, make_aware

from dataprocessor.models import DataEntry

colorama.init()

COLOR = {
    "HEADER": "\033[95m",
    "BLUE": "\033[94m",
    "CYAN": "\033[96m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "PURPLE": "\033[35m",
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
    "UNDERLINE": "\033[4m"
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)

GRADE_MAPPING = {"F": 0, "D": 1, "C": 2, "B": 3, "A": 4}
REVERSE_GRADE_MAPPING = {v: k for k, v in GRADE_MAPPING.items()}


def is_valid_url(url):
    """Validate and parse URL structure."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception as e:
        logger.error(f"{COLOR['RED']}URL parsing error: {e}{COLOR['RESET']}")
        return False


class Command(BaseCommand):
    help = "Process XML/JSON data with validation and grading system"

    def handle(self, *args, **kwargs):
        logger.info(f"{COLOR['BLUE']}=== Starting data processing pipeline ==={COLOR['RESET']}")
        self.process_file("input-sample1.xml", self.parse_xml)
        self.process_file("input-sample3.json", self.parse_json)
        logger.info(f"{COLOR['GREEN']}=== Processing complete. Total entries: {DataEntry.objects.count()} ==={COLOR['RESET']}")

    def process_file(self, filepath, parser):
        """Execute file processing with error handling."""
        file_type = filepath.split(".")[-1].upper()
        logger.info(f"{COLOR['CYAN']}Processing {file_type} file: {filepath}{COLOR['RESET']}")
        
        try:
            parser(filepath)
        except ET.ParseError as pe:
            logger.error(f"{COLOR['RED']}XML parsing error: {pe}{COLOR['RESET']}")
            raise
        except json.JSONDecodeError as jde:
            logger.error(f"{COLOR['RED']}JSON parsing error: {jde}{COLOR['RESET']}")
            raise
        except Exception as e:
            logger.error(f"{COLOR['RED']}File processing failed: {e}{COLOR['RESET']}")
            raise

    def parse_xml(self, filepath):
        """Process XML file entries."""
        tree = ET.parse(filepath)
        items = tree.getroot().findall("item")
        logger.info(f"{COLOR['CYAN']}Found {len(items)} XML entries{COLOR['RESET']}")

        for idx, item in enumerate(items, 1):
            self.process_entry({
                "unique_id": item.findtext("string6"),
                "dataString0": item.findtext("string0"),
                "dataString1": item.findtext("string1"),
                "dataString2": item.findtext("string2"),
                "dataString3": item.findtext("string3"),
                "dataString4": item.findtext("string4"),
                "dataString5": item.findtext("string5"),
                "status": item.findtext("status"),
            }, idx, "XML")

    def parse_json(self, filepath):
        """Process JSON file entries."""
        with open(filepath, "r") as f:
            entries = json.load(f)
            logger.info(f"{COLOR['CYAN']}Found {len(entries)} JSON entries{COLOR['RESET']}")

            for idx, entry in enumerate(entries, 1):
                self.process_entry({
                    "unique_id": entry.get("dataString6"),
                    "dataString0": entry.get("dataString0"),
                    "dataString1": entry.get("dataString1"),
                    "dataString2": entry.get("dataString2"),
                    "dataString3": entry.get("dataString3"),
                    "dataString4": entry.get("dataString4"),
                    "dataString5": entry.get("dataString5"),
                    "status": entry.get("status"),
                }, idx, "JSON")

    def process_entry(self, data, entry_num, source_format):
        """Validate, grade, and store data entry."""
        entry_id = data.get("unique_id") or f"Entry-{entry_num}-{source_format}"
        logger.info(f"\n{COLOR['CYAN']}--- Processing {entry_id} ---{COLOR['RESET']}")

        if data.get("status") == "-1":
            logger.warning(f"{COLOR['YELLOW']}Skipping entry with status -1{COLOR['RESET']}")
            return

        required_fields = {
            "URL": data.get("dataString0"),
            "DateTime": data.get("dataString1"),
            "PostalCode": data.get("dataString3")
        }
        if missing := [k for k, v in required_fields.items() if not v]:
            logger.error(f"{COLOR['RED']}Missing fields: {', '.join(missing)}{COLOR['RESET']}")
            return

        unique_id = data.get("unique_id") or str(uuid.uuid4())
        if not data.get("unique_id"):
            logger.info(f"{COLOR['PURPLE']}Generated UUID: {unique_id}{COLOR['RESET']}")

        try:
            parsed_dt = date_parser.parse(data["dataString1"], fuzzy=True)
            parsed_dt = make_aware(parsed_dt) if is_naive(parsed_dt) else parsed_dt
            logger.debug(f"{COLOR['CYAN']}Parsed datetime: {parsed_dt}{COLOR['RESET']}")
        except Exception as e:
            logger.error(f"{COLOR['RED']}DateTime error: {e}{COLOR['RESET']}")
            return

        numeric_value = None
        if raw_value := data.get("dataString5"):
            try:
                numeric_value = Decimal(raw_value).quantize(Decimal("1"))
                logger.debug(f"{COLOR['CYAN']}Numeric value: {numeric_value}{COLOR['RESET']}")
            except (InvalidOperation, ValueError) as e:
                logger.error(f"{COLOR['RED']}Numeric error: {e}{COLOR['RESET']}")
                return

        grade_result = self.grade_entry(data)
        logger.info(f"{COLOR['PURPLE']}Final grade: {grade_result['letter_grade']} ({grade_result['final_grade']}){COLOR['RESET']}")

        try:
            obj, created = DataEntry.objects.update_or_create(
                unique_id=unique_id,
                defaults={
                    "dataString0": data["dataString0"],
                    "dataString1": parsed_dt,
                    "dataString2": data.get("dataString2", ""),
                    "dataString3": data["dataString3"],
                    "dataString4": data.get("dataString4", ""),
                    "dataString5": numeric_value,
                    "grade": grade_result["final_grade"],
                }
            )
            action = "Created" if created else "Updated"
            logger.info(f"{COLOR['GREEN']}{action} entry: {unique_id}{COLOR['RESET']}")
        except Exception as e:
            logger.error(f"{COLOR['RED']}Database error: {e}{COLOR['RESET']}")

    def grade_entry(self, data):
        """Calculate data quality grades for each field."""
        grades = {}
        reasons = {}

        # URL validation
        url = data.get("dataString0")
        if not url:
            grades["dataString0"], reasons["dataString0"] = GRADE_MAPPING["F"], f"{COLOR['RED']}Missing URL{COLOR['RESET']}"
        else:
            valid_url = is_valid_url(url)
            grade = GRADE_MAPPING["A"] if valid_url else GRADE_MAPPING["D"]
            reason = f"{COLOR['GREEN']}Valid URL{COLOR['RESET']}" if valid_url else f"{COLOR['YELLOW']}Invalid URL{COLOR['RESET']}"
            grades["dataString0"], reasons["dataString0"] = grade, reason

        # DateTime validation
        dt_str = data.get("dataString1")
        if not dt_str:
            grades["dataString1"], reasons["dataString1"] = GRADE_MAPPING["F"], f"{COLOR['RED']}Missing DateTime{COLOR['RESET']}"
        else:
            try:
                date_parser.parse(dt_str, fuzzy=False)
                grades["dataString1"], reasons["dataString1"] = GRADE_MAPPING["A"], f"{COLOR['GREEN']}Valid DateTime{COLOR['RESET']}"
            except Exception as e:
                grades["dataString1"], reasons["dataString1"] = GRADE_MAPPING["C"], f"{COLOR['YELLOW']}Invalid format: {e}{COLOR['RESET']}"

        # Category validation
        category = data.get("dataString2")
        if not category:
            grades["dataString2"], reasons["dataString2"] = GRADE_MAPPING["B"], f"{COLOR['YELLOW']}Missing category{COLOR['RESET']}"
        else:
            valid = category.isprintable()
            grade = GRADE_MAPPING["A"] if valid else GRADE_MAPPING["B"]
            reason = f"{COLOR['GREEN']}Valid category{COLOR['RESET']}" if valid else f"{COLOR['YELLOW']}Invalid characters{COLOR['RESET']}"
            grades["dataString2"], reasons["dataString2"] = grade, reason

        # Postal code validation
        postal_code = data.get("dataString3", "")
        digits = sum(c.isdigit() for c in postal_code)
        letters = sum(c.isalpha() for c in postal_code)
        if not postal_code:
            grades["dataString3"], reasons["dataString3"] = GRADE_MAPPING["F"], f"{COLOR['RED']}Missing postal code{COLOR['RESET']}"
        else:
            valid = digits >= 4 and letters >= 2
            grade = GRADE_MAPPING["A"] if valid else GRADE_MAPPING["C"]
            status = f"({digits}/4 digits, {letters}/2 letters)"
            reason = f"{COLOR['GREEN']}Valid {status}{COLOR['RESET']}" if valid else f"{COLOR['YELLOW']}Invalid {status}{COLOR['RESET']}"
            grades["dataString3"], reasons["dataString3"] = grade, reason

        # Optional field validation
        opt_field = data.get("dataString4", "")
        if not opt_field:
            grades["dataString4"], reasons["dataString4"] = GRADE_MAPPING["B"], f"{COLOR['YELLOW']}Missing optional field{COLOR['RESET']}"
        else:
            valid_length = 5 <= len(opt_field) <= 40
            valid_chars = opt_field.isprintable()
            grade = GRADE_MAPPING["A"] if valid_length and valid_chars else GRADE_MAPPING["B"]
            reason = (
                f"{COLOR['GREEN']}Valid field{COLOR['RESET']}" if valid_length and valid_chars else
                f"{COLOR['YELLOW']}Invalid length" if not valid_length else
                f"{COLOR['YELLOW']}Invalid characters"
            )
            grades["dataString4"], reasons["dataString4"] = grade, reason

        # Numeric field validation
        num_field = data.get("dataString5")
        if not num_field:
            grades["dataString5"], reasons["dataString5"] = GRADE_MAPPING["B"], f"{COLOR['YELLOW']}Missing numeric{COLOR['RESET']}"
        else:
            try:
                num = float(num_field)
                valid = num.is_integer()
                grade = GRADE_MAPPING["A"] if valid else GRADE_MAPPING["B"]
                reason = f"{COLOR['GREEN']}Valid integer{COLOR['RESET']}" if valid else f"{COLOR['YELLOW']}Non-integer{COLOR['RESET']}"
                grades["dataString5"], reasons["dataString5"] = grade, reason
            except ValueError:
                grades["dataString5"], reasons["dataString5"] = GRADE_MAPPING["B"], f"{COLOR['YELLOW']}Invalid numeric{COLOR['RESET']}"

        final_grade = min(grades.values())
        letter_grade = REVERSE_GRADE_MAPPING[final_grade]

        logger.info(f"{COLOR['BLUE']}=== Grading Report ===")
        for field in ["dataString0", "dataString1", "dataString2", "dataString3", "dataString4", "dataString5"]:
            logger.info(
                f"{COLOR['CYAN']}{field:<12}{COLOR['RESET']} | "
                f"Grade: {COLOR['PURPLE']}{REVERSE_GRADE_MAPPING[grades[field]]:<1}{COLOR['RESET']} | "
                f"{reasons[field]}"
            )
        logger.info(f"{COLOR['BLUE']}====================={COLOR['RESET']}")

        return {
            "final_grade": final_grade,
            "letter_grade": letter_grade,
            "details": reasons
        }