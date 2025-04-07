from django.db import models

GRADE_MAPPING = {
    0: "F",
    1: "D",
    2: "C",
    3: "B",
    4: "A"
}

class DataEntry(models.Model):
    """Represents a data entry with validated fields and quality grading."""
    
    unique_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Unique Identifier"
    )
    dataString0 = models.URLField(
        verbose_name="URL"
    )
    dataString1 = models.DateTimeField(
        verbose_name="Timestamp"
    )
    dataString2 = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Category"
    )
    dataString3 = models.CharField(
        max_length=20,
        verbose_name="Postal Code"
    )
    dataString4 = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        verbose_name="Optional Field"
    )
    dataString5 = models.DecimalField(
        max_digits=40,
        decimal_places=0,
        blank=True,
        null=True,
        verbose_name="Numeric Value"
    )
    grade = models.IntegerField(
        help_text="Quality grade (0=F, 4=A)"
    )

    class Meta:
        verbose_name = "Data Entry"
        verbose_name_plural = "Data Entries"
        ordering = ["-dataString1"]

    def __str__(self) -> str:
        return f"{self.dataString0} ({self.letter_grade})"

    @property
    def letter_grade(self) -> str:
        """Get human-readable quality grade letter."""
        return GRADE_MAPPING.get(self.grade, "?")