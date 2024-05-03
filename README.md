# snapQuery
Tool that helps users preview, explore queries, and enlist expert help in Wikidata queries seamlessly. Trust query stability with past performance insights and community feedback. Annotate, rate, and collaborate easily. Developers and data consumers can get access to the data via APIs.

## Features
### Planned
These are the planned features
* query multiple backends simultaneously and repeatedly
* stores queries and adaptations needed for different backends
* support user login
* support for spam protection
* support for naming queries
* support for rating queries
* support for sharing queries (unique identifier)
* support for commenting on queries
* support for detecting when a query returns different results between different backends
* support for query states: reliable, needs investigation, need verification
* support for autodetecting when a query returns fewer results than before (change in underlying data/model in Wikidata) -> needs investigation
* support for marking queries as reliable query by users
* support for seeing a state history per query
* support for storing query results so you don’t have to wait
* support for adding metadata to queries
  * add main subject (QID) to query
  * author -> id of author in the system
  * forked from x
* has REST API for data consumers e.g. LLM developers who want to present user-verified queries and data to users to increase reliability
