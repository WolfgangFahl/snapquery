"""
Created on 2024-05-01

@author: wf
"""

from dataclasses import dataclass

import snapquery


@dataclass
class Version:
    """
    Version handling for snapquery
    """

    name = "snapquery"
    version = snapquery.__version__
    date = "2024-05-03"
    updated = "2025-12-11"
    description = "Introduce Named Queries and Named Query Middleware to wikidata"

    authors = "Wolfgang Fahl"

    doc_url = "https://wiki.bitplan.com/index.php/snapquery"
    chat_url = "https://github.com/WolfgangFahl/snapquery/discussions"
    cm_url = "https://github.com/WolfgangFahl/snapquery"

    license = """Copyright 2024-2025 contributors. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied."""

    longDescription = f"""{name} version {version}
{description}

  Created by {authors} on {date} last updated {updated}"""
