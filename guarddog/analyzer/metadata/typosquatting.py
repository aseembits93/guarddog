import abc
from itertools import permutations

from guarddog.analyzer.metadata.detector import Detector


class TyposquatDetector(Detector):
    MESSAGE_TEMPLATE = "This package closely resembles the following package names, and might be a typosquatting " \
                       "attempt: %s"

    def __init__(self) -> None:
        self.popular_packages = self._get_top_packages()  # Find top PyPI packages
        super().__init__(
            name="typosquatting",
            description="Identify packages that are named closely to an highly popular package"
        )

    @abc.abstractmethod
    def _get_top_packages(self) -> set:
        pass

    def _is_distance_one_Levenshtein(self, name1, name2) -> bool:
        """
        Returns True if two names have a Levenshtein distance of one

        Args:
            name1 (str): first name
            name2 (str): second name

        Returns:
            bool: True if within distance one
        """

        len1, len2 = len(name1), len(name2)
        if abs(len1 - len2) > 1:
            return False

        # Addition to name2
        if len1 > len2:
            # Can we make name1==name2 by deleting one char from name1?
            for i in range(len1):
                # Compare parts before and after the skipped char
                if name1[:i] == name2[:i] and name1[i+1:] == name2[i:]:
                    return True
            return False

        # Addition to name1
        elif len2 > len1:
            for i in range(len2):
                if name2[:i] == name1[:i] and name2[i+1:] == name1[i:]:
                    return True
            return False

        # Same length: check for one substitution or one deletion+insertion at the same spot
        else:
            mismatch = 0
            for i in range(len1):
                if name1[i] != name2[i]:
                    mismatch += 1
                    if mismatch > 1:
                        return False
            if mismatch == 1:
                return True
            # Now check if exactly one deletion + one insertion at same spot (i.e. one transposition)
            for i in range(len1):
                if name1[:i] == name2[:i] and name1[i+1:] == name2[i+1:]:
                    return True
            return False

    def _is_swapped_typo(self, name1, name2) -> bool:
        """
        Returns true is two names are adjacent swaps of each other

        Args:
            name1 (str): first name
            name2 (str): second name

        Returns:
            bool: True if adjacent swaps
        """
        len1 = len(name1)
        if len1 != len(name2):
            return False
        for i in range(len1-1):
            if (name1[i] != name2[i] or name1[i+1] != name2[i+1]) and \
               (name1[i+1] == name2[i] and name1[i] == name2[i+1]):
                # Only allow exactly this adjacent swap, and the rest must match
                if i == 0:
                    tail_equal = name1[2:] == name2[2:]
                elif i == len1-2:
                    head_equal = name1[:i] == name2[:i]
                    tail_equal = True
                else:
                    head_equal = name1[:i] == name2[:i]
                    tail_equal = name1[i+2:] == name2[i+2:]
                if (i == 0 or head_equal) and tail_equal:
                    return True
        return False

    def _generate_permutations(self, package_name) -> list[str]:
        """
        Generates all permutations of hyphenated terms of a package

        Args:
            package_name (str): name of package

        Returns:
            list[str]: permutations of package_name
        """

        if "-" not in package_name:
            return []

        components = package_name.split("-")
        hyphen_permutations = ["-".join(p) for p in permutations(components)]

        return hyphen_permutations

    def _is_length_one_edit_away(self, package1, package2) -> bool:
        """
        Returns True if two packages are within a distance one typo edit
        (either within a Levenshtein distance of one or an adjacent swap edit)

        Args:
            package1 (str): first package name
            package2 (str): second package name

        Returns:
            bool: True
        """

        return self._is_distance_one_Levenshtein(package1, package2) or self._is_swapped_typo(package1, package2)

    @abc.abstractmethod
    def _get_confused_forms(self, package_name) -> list:
        pass

    def get_typosquatted_package(self, package_name) -> list[str]:
        """
        Gets all legitimate packages that a given name
        is possibly typosquatting from

        Checks for Levenshtein distance, permutations, and confused terms
        against the top 5000 most downloaded PyPI packages

        Args:
            package_name (str): name of package

        Returns:
            list[str]: names of packages that <package_name> could be
            typosquatting from
        """

        if package_name in self.popular_packages:
            return []

        # Go through popular packages and find length one edit typosquats
        typosquatted = set()
        for popular_package in self.popular_packages:
            if self._is_length_one_edit_away(package_name, popular_package):
                typosquatted.add(popular_package)

            alternate_popular_names = self._get_confused_forms(popular_package)
            swapped_popular_names = self._generate_permutations(popular_package)

            for name in alternate_popular_names + swapped_popular_names:
                if self._is_length_one_edit_away(package_name, name):
                    typosquatted.add(popular_package)

        return list(typosquatted)
