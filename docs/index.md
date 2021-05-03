---
hide-toc: true
---

# Welcome to installer's documentation

```{include} ../README.md
:start-after: <!-- start readme-pitch -->
:end-before: <!-- end readme-pitch -->
```

```{toctree}
:hidden:

concepts
```

```{toctree}
:caption: API reference
:hidden:
:glob:

api/*
```

```{toctree}
:caption: Project
:hidden:

development/index
changelog
license
GitHub <https://github.com/pradyunsg/installer>
PyPI <https://pypi.org/project/installer>
```

## Basic Usage

```python
import sysconfig

from installer import install
from installer.destinations import SchemeDictDestination
from installer.sources import WheelFile

# This represents the wheel file, and handle reading from it.
source = WheelFile("sampleproject-1.3.1-py2.py3-none-any.whl")

# This represents the installation directories, and writes to them.
destination = SchemeDictDestination(sysconfig.get_config_vars())

# This is the additional metadata, generated during installation.
additional_metadata = {
    "INSTALLER": b"amazing-installer 0.1.0",
}

install(
    source=source,
    destination=destination,
    additional_metadata=additional_metadata,
)
```

```{attention}
The `WheelFile` class mentioned above has not been implemented yet.
Contributions are welcome!
```
