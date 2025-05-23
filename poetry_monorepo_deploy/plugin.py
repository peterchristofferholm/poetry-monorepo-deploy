from poetry.console.application import Application
from poetry.plugins.application_plugin import ApplicationPlugin

from poetry_monorepo_deploy.commands.buildproject import project


class MultiProjectPlugin(ApplicationPlugin):
    """Poetry Multiproject plugin
    A plugin that adds the "build-project" command.

    The command will make it possible to use relative package includes.
    This feature is very useful for monorepos and using shared code.

    Usage
    Navigate to the project folder and run: poetry build-project
    """

    def activate(self, application: Application):
        application.command_loader.register_factory(
            project.command_name,
            project.ProjectBuildCommand,
        )
