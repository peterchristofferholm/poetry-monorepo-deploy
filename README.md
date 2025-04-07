# Poetry Multiproject Plugin

This is a Python `Poetry` plugin, adding the `deploy-project`.

The `deploy-project` command will make it possible to use relative package includes.
This feature is very useful for monorepos and when sharing code between projects.

## Use cases

### Microservices and apps
The main use case is to support having one or more microservices or apps in a Monorepo, and share code between the services with namespaced packages.
The `deploy-project` command will collect the project-specific packages and build an deployable folder from it (e.g. Azure Function App) .

### How is it different from the "poetry build" command?
Poetry does not allow package includes outside of the __project__ root.

``` shell
# Note the structure of the shared folder: namespace/package

packages = [
    { include = "my_namespace/my_package", from = "../../shared" }
    { include = "my_namespace/my_other_package", from = "../../shared" }
]
```

This plugin will allow relative package includes. You will now be able to share code between projects.

### Organizing code

An example Monorepo structure, having the shared code extracted into a separate folder structure:

``` shell
projects/
  my_app/
    pyproject.toml (including selected shared packages)

  my_service/
    pyproject.toml (including selected shared packages)

shared/
  my_namespace/
    my_package/
      __init__.py
      code.py

    my_other_package/
      __init__.py
      code.py
```
