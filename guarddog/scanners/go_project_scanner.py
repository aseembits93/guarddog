import logging
import os
import re
from dataclasses import dataclass
from typing import List

from guarddog.scanners.go_package_scanner import GoModuleScanner
from guarddog.scanners.scanner import ProjectScanner
from guarddog.scanners.scanner import Dependency, DependencyVersion

log = logging.getLogger("guarddog")


@dataclass
class GoRequirement:
    module: str
    version: str


@dataclass
class GoModule:
    module: str
    go: str
    toolchain: str
    requirements: List[GoRequirement]


class GoDependenciesScanner(ProjectScanner):
    def __init__(self) -> None:
        super().__init__(GoModuleScanner())

    def parse_requirements(self, raw_requirements: str) -> List[Dependency]:
        main_mod = self.parse_go_mod_file(raw_requirements)

        # Preprocess: Map from dependency name to the first (line) index (0-based)
        first_line_for_module = {}
        for ix, line in enumerate(raw_requirements.splitlines()):
            # Optimize: only care about lines that look like an import
            # "require github.com/foo/bar v1.2.3", "github.com/foo/bar v1.2.3" inside require block, etc.
            # This is conservative: we just record every module occurrence & first line
            parts = line.strip().split()
            # The name of module will be 1 in "require X Y", or 0 in "X Y" inside require ( ... )
            if len(parts) >= 2:
                # check for "require mod version" (outside block)
                if parts[0] == "require":
                    name = parts[1]
                else:
                    name = parts[0]
                if name not in first_line_for_module:
                    first_line_for_module[name] = ix

        # Optimize: maintain dependencies by name for O(1) update/lookup
        dependencies_map = {}
        dependencies: List[Dependency] = []
        for dependency in main_mod.requirements:
            version = dependency.version
            name = dependency.module
            idx = first_line_for_module.get(name, 0)

            dep_versions = [DependencyVersion(version=version, location=idx + 1)]

            if name not in dependencies_map:
                dep = Dependency(name=name, versions=set())
                dependencies_map[name] = dep
                dependencies.append(dep)
            else:
                dep = dependencies_map[name]

            dep.versions.update(dep_versions)
        return dependencies

    # Read https://go.dev/ref/mod#go-mod-file to learn more about the go.mod syntax
    def parse_go_mod_file(self, go_mod_content: str) -> GoModule:
        module = ""
        go = ""
        toolchain = ""
        requirements = []

        is_in_block = None
        for line in go_mod_content.splitlines():
            line = line.strip()

            if line.startswith("//"):  # Ignore comments
                continue
            elif line.startswith("module "):
                module = line.split()[1]
            elif line.startswith("go "):
                go = line.split()[1]
            elif line.startswith("toolchain "):
                toolchain = line.split()[1]
            elif line.startswith("require ("):
                is_in_block = "require"
            elif line.startswith("require "):
                parts = line.split()
                requirements.append(GoRequirement(parts[1], parts[2]))
            elif line.endswith(")") and is_in_block:
                is_in_block = None
            elif is_in_block == "require" and line != "":
                parts = line.split()
                requirements.append(GoRequirement(parts[0], parts[1]))
            # TODO: support exclude, replace and retract statements

        return GoModule(module, go, toolchain, requirements)

    def find_requirements(self, directory: str) -> list[str]:
        requirement_files = []
        for root, dirs, files in os.walk(directory):
            for name in files:
                if re.match(r"^go\.mod$", name, flags=re.IGNORECASE):
                    requirement_files.append(os.path.join(root, name))
        return requirement_files
