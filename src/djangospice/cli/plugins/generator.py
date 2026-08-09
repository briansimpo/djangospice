import json
import logging
from pathlib import Path
from .metadata import DjangoAppConfig, PluginConfig
from .pip import pip_install_editable
from .utils import copy_file,generate_stub, generate_stubs,pascal_case, verbose_case


logger = logging.getLogger(__name__)


class PluginGenerator:
    """
    Create a new djangospice plugin with the djangospice architecture.
    """
    PYTHON_VERSION = "3.12"
    DEFAULT_NAMESPACE = "djangospice"
    DEFAULT_STUBS_DIR = "stubs/plugin"

    def __init__(self, config: PluginConfig, stubs_dir: Path | str = None, dry_run: bool = False):
        
        self.config = config

        self.dry_run = dry_run

        # Stubs paths
        if stubs_dir is None:
            stubs_dir = self.DEFAULT_STUBS_DIR
        
        self.stubs_dir = Path(stubs_dir)

        # Official namespace
        self.namespace = self.DEFAULT_NAMESPACE

        self.normalized_name = self.config.name.lower().replace("-", "_")

        # Base directory for plugin creation
        self.output_dir = Path(self.config.output_dir) if self.config.output_dir else Path.cwd()
        
        # Derived attributes
        self.module_name = ""
        self.short_name = ""
        self.repo_name = ""
        self.pkg_name = ""
        self.pkg_dir: Path = None

    def _resolve_names(self):
        # Decide namespace parts
        if self.config.official:
            parts = self.normalized_name.split(".")

            # Ensure starts with official namespace
            if parts[0] != self.namespace:
                if parts[0].startswith(f"{self.namespace}_"):
                    first_part = parts[0][len(f"{self.namespace}_"):]
                    parts = [self.namespace] + ([first_part] if first_part else []) + parts[1:]
                else:
                    parts = [self.namespace] + parts

        elif "." in self.normalized_name:
            # Community namespaced
            parts = self.normalized_name.split(".")

        else:
            # Community flat
            parts = [self.normalized_name]

        # Save attributes
        self.module_name = ".".join(parts)
        self.short_name = parts[-1]
        self.pkg_name = "_".join(parts)
        self.repo_name = self.pkg_name.replace("_", "-")

        # Top-level output folder (repo)
        self.output_dir = Path(self.output_dir) / self.repo_name 

        # Package directory inside output
        if len(parts) == 1 and not self.config.official:
            # flat community plugin → one folder inside output
            self.pkg_dir = self.output_dir / self.pkg_name
        else:
            # official + namespaced community
            self.pkg_dir = self.output_dir / Path(*parts)

        self.config.pkg_name = self.pkg_name
        self.config.repo_name = self.repo_name

    def _create_directories(self):
        """Create plugin directories like templates, static, media."""
        if self.dry_run:
            logger.info(f"[dry-run] Would create directories under {self.pkg_dir}")
            for d in ("templates", "static", "media"):
                logger.info(f"[dry-run]  - {self.pkg_dir / d}")
        else:
            for d in ("templates", "static", "media"):
                (self.pkg_dir / d).mkdir(parents=True, exist_ok=True)

    def _generate_stubs(self):
        """Write pyproject.toml, plugin.json, and generate stubs."""
        
        app_config = DjangoAppConfig(
            class_name=pascal_case(self.normalized_name),
            module_name=self.module_name,
            module_label=self.short_name.lower(),
            verbose_name=verbose_case(self.short_name),
        )

        kwargs = app_config.to_dict()

        if self.dry_run:
            logger.info(f"[dry-run] Would generate stubs from {self.stubs_dir} to {self.pkg_dir} with args: {kwargs}")
        else:
            generate_stubs(self.stubs_dir, self.pkg_dir, **kwargs)

    def _generate_pyproject(self):
        if self.dry_run:
            logger.info(f"[dry-run] Would write {self.output_dir / 'pyproject.toml'}")
        else:
            pyproject_stub = self.stubs_dir / "pyproject.txt"
            pyproject_file = self.output_dir / "pyproject.toml"
            kwargs = {"plugin": self.config}
            generate_stub(pyproject_stub, pyproject_file, **kwargs)

    def _generate_plugin_json(self):
        if self.dry_run:
            logger.info(f"[dry-run] Would write {self.pkg_dir / 'plugin.json'}")
        else:
            plugin_stub = self.stubs_dir / "plugin.txt"
            plugin_file = self.pkg_dir / "plugin.json"
            kwargs = {"plugin": self.config}
            generate_stub(plugin_stub, plugin_file, **kwargs)

    def _generate_read_me(self):
        if self.dry_run:
            logger.info(f"[dry-run] Would write {self.output_dir / 'README.md'}")
        else:
            readme_stub = self.stubs_dir / "readme.txt"
            readme_file = self.output_dir / "README.md"
            kwargs = {"plugin": self.config}
            generate_stub(readme_stub, readme_file, **kwargs)
           
    def _copy_git_ignore(self):
        git_ignore_stub = self.stubs_dir / "gitignore.txt"
        git_ignore_file = self.output_dir / ".gitignore"
        if self.dry_run:
            logger.info(f"[dry-run] Would copy {git_ignore_stub} → {git_ignore_file}")
        else:
            copy_file(git_ignore_stub, git_ignore_file)

    def summary(self) -> dict:
        """Return plugin metadata and paths before creation."""
        self._resolve_names()

        return {
            "name": self.config.name,
            "repo_name": self.repo_name,
            "pkg_name": self.pkg_name,
            "module_name": self.module_name,
            "namespace": self.namespace,
            "official": self.config.official,
            "editable": self.config.editable,
            "output_dir": str(self.output_dir),
            "pkg_dir": str(self.pkg_dir),
            "stubs_dir": str(self.stubs_dir),
            "dry_run": self.dry_run
        }

    def print_summary(self):
        summary_dict = self.summary()
        print(json.dumps(summary_dict, indent=4))

    def generate(self):
        """Orchestrate plugin creation."""
        self._resolve_names()
        self._create_directories()
        self._generate_stubs()
        self._generate_plugin_json()
        self._generate_pyproject()
        self._generate_read_me()
        self._copy_git_ignore()

        if self.dry_run:
            logger.info(f"[dry-run] Plugin creation simulated for {self.pkg_name} at {self.output_dir}")
            self.print_summary()
        else:
            logger.info(f"Created {self.pkg_name} at {self.output_dir}")
            if self.config.editable:
                pip_install_editable(self.output_dir)
