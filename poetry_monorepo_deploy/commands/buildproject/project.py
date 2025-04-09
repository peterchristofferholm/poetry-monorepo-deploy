from pathlib import Path
from typing import List, Union
import os
import shutil

from cleo.helpers import option
from cleo.io.inputs.option import Option
from poetry.console.commands.build import BuildCommand
from poetry.factory import Factory
from poetry.core.masonry.builders.builder import Builder
from poetry.installation.installer import Installer
from poetry.utils.env import EnvManager, VirtualEnv

from poetry.exceptions import PoetryError

from poetry_monorepo_deploy.components import parsing
from poetry_monorepo_deploy.components.project import (
    cleanup,
    create,
    packages,
    prepare,
)

command_name = "deploy-project"


def create_command_options() -> List[Option]:
    parent = BuildCommand.options or []

    current = [
        option(
            long_name="with-top-namespace",
            description="To arrange relative includes, and to modify import statements.",
            flag=False,
        ),
        option(
            long_name="with-venv",
            description="Should the build project also make a .venv folder with dependencies?",
            flag=True,
        )
    ]

    return parent + current


class ProjectBuildCommand(BuildCommand):
    name = command_name

    options = create_command_options()

    def collect_project(self, path: Path, top_ns: Union[str, None]) -> Path:
        destination = prepare.get_destination(path, "prepare")

        prepare.copy_project(path, destination)
        packages.copy_packages(path, destination, top_ns)
        self.line(
            f"Copied project and packages into temporary folder <c1>{destination}</c1>"
        )

        generated = create.create_new_project_file(path, destination, top_ns)
        self.line(f"Generated <c1>{generated}</c1>")

        return destination

    def rewrite_modules(self, project_path: Path, top_ns: str) -> None:
        folder = project_path / top_ns

        if not folder.exists():
            return

        self.line(f"Using normalized top namespace: {top_ns}")
        namespaces = [item.name for item in folder.iterdir() if item.is_dir()]

        modules = folder.glob("**/*.py")

        for module in modules:
            was_rewritten = parsing.rewrite_module(module, namespaces, top_ns)
            if was_rewritten:
                self.line(
                    f"Updated <c1>{module.parent.name}/{module.name}</c1> "
                    "with new top namespace for local imports."
                )

    def prepare_for_build(self, path: Path):
        project_poetry = Factory().create_poetry(path)

        if hasattr(self, "set_poetry"):
            self.set_poetry(project_poetry)
        elif hasattr(self, "_poetry"):
            self._poetry = project_poetry
        else:
            raise ValueError("Cannot find expected Poetry Command internals.")

    def copy_files(self):
        builder = Builder(poetry=self.poetry)
        files = builder.find_files_to_add()

        target_dir = Path(self.option("output"))
        self.line(f"Target directory <c1>{target_dir}</c1>")

        for file in files:
            src_path = file.path

            dst_path = target_dir / file.relative_to_project_root()
            dst_path.parent.mkdir(exist_ok=True, parents=True)

            shutil.copy2(src_path, dst_path)

        self.line("Copied <c1>dist</c1> folder.")

    def create_venv(self):

        # find root pyproject.toml
        current_path = self.poetry.file.path.parent
        while current_path != current_path.parent:
            parent_pyproject = current_path / "pyproject.toml"
            if parent_pyproject.exists() and parent_pyproject != self.poetry.file.path:
                parent_poetry = Factory().create_poetry(parent_pyproject)
                break
            else: 
                current_path = current_path.parent
        else:
            raise PoetryError("Couldn't find a root pyproject.toml")

        # setup virtual env
        venv_path = Path(self.option("output")) / ".venv"
        if not venv_path.exists():
            self.line(f"<info>Creating virtual environment at {venv_path}</info>")
            env_manager = EnvManager(self.poetry, self.io)
            env_manager.build_venv(path=venv_path)
        else:
            self.line(f"<info>Using existing virtual environment at {venv_path}</info>")

        venv = VirtualEnv(venv_path)
        installer = Installer(
            self.io,
            venv,
            parent_poetry.package,
            self.poetry.locker,
            parent_poetry.pool,
            parent_poetry.config,
        )
        # installer._update = True
        # installer._lock = True
        installer.run()

    def handle(self):
        path = self.poetry.file.path.absolute()
        self.line(f"Using <c1>{path}</c1>")
        self.line(f"Current package: <c1>{self.poetry.package}</c1>")
        self.line(f"Working directory <c1>{os.getcwd()}</c1>")

        top_ns = prepare.normalize_top_namespace(self.option("with-top-namespace"))
        project_path = self.collect_project(path, top_ns)

        if self.option("with-venv"):
            self.create_venv()

        self.prepare_for_build(project_path.absolute())

        if top_ns:
            self.rewrite_modules(project_path, top_ns)

        self.copy_files()

        cleanup.remove_project(project_path)
        self.line("Removed temporary folder.")
        self.line("<c1>Done!</c1>")
