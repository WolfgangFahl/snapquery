# snapQuery
Just query wikidata by name of query ... 
<pre>snapquery cats</pre> is all you need 

This endpoint and query detail independent style of querying wikidata and ther SPARQL services 
makes your queries future proof. No worries about blazegraph being replaced, the graph being split or timeouts haunting you. snapquery introduces named queries and named query middleware to wikidata and other SPARQL endpoints 

snapquery is a tool that simplifies the process of previewing, annotating, rating, commenting, running, and exploring Wikidata
queries across different SPARQL backends. It enhances user experience by storing query results and allowing easy
comparison across various backends and over time.

This tool is designed to assist users in curating and collaborating on queries, ensuring their continued functionality
over time. Developers and data consumers can access data conveniently through APIs, streamlining their workflow.

[![Join the discussion at https://github.com/WolfgangFahl/snapquery/discussions](https://img.shields.io/github/discussions/WolfgangFahl/snapquery)](https://github.com/WolfgangFahl/snapquery/discussions)
[![pypi](https://img.shields.io/pypi/pyversions/snapquery)](https://pypi.org/project/snapquery/)
[![Github Actions Build](https://github.com/WolfgangFahl/snapquery/actions/workflows/build.yml/badge.svg)](https://github.com/WolfgangFahl/snapquery/actions/workflows/build.yml)
[![PyPI Status](https://img.shields.io/pypi/v/snapquery.svg)](https://pypi.python.org/pypi/snapquery/)
[![GitHub issues](https://img.shields.io/github/issues/WolfgangFahl/snapquery.svg)](https://github.com/WolfgangFahl/snapquery/issues)
[![GitHub issues](https://img.shields.io/github/issues-closed/WolfgangFahl/snapquery.svg)](https://github.com/WolfgangFahl/snapquery/issues/?q=is%3Aissue+is%3Aclosed)
[![GitHub](https://img.shields.io/github/license/WolfgangFahl/snapquery)](https://www.apache.org/licenses/LICENSE-2.0)

## Demos

* [wikimedia toolhub](https://toolhub.wikimedia.org/tools/snapquery)
* [BITPlan](https://snapquery.bitplan.com)
* [RWTH Aachen i5](https://snapquery.wikidata.dbis.rwth-aachen.de/)

## Background

In the Wikimedia ecosystem, we now boast several SPARQL engines and backends housing the complete Wikidata graph for
querying purposes.

Over recent years, WDQS has encountered escalating timeouts as the graph expands. Users desire alternative endpoints
without grappling with disparities among SPARQL engines and their impact on query construction.

Recognizing the needs of Wikidata data consumers, we aim to establish a system that simplifies:

- Discovering pre-existing queries
- Facilitating easy forking, sharing, rating, and monitoring of queries
- Executing queries (or their variations) on diverse endpoints
- Comparing query results over time and/or across multiple endpoints
- Cultivating a collaborative community for query construction
- Ensuring the reliability of query results
- Providing alerts if a query no longer yields the expected results
- Developing tools that access data from dependable, middleware-cached
  queries via an accessible API, eliminating delays for downstream users.

# Links

* [Phabricator Task: Introduce Named Queries and Named Query Middleware to wikidata](https://phabricator.wikimedia.org/T363894)
* [Named Queries prototype by Tim Holzheim](https://github.com/tholzheim/named-queries/tree/master)

## Docs

* [Wiki](https://wiki.bitplan.com/index.php/Snapquery)
* [API documentation](https://snapquery.bitplan.com/docs)
* [Wikimedia Hackathon 2024 closing presentation](https://docs.google.com/presentation/d/1hVoIwRHjmA8x2scl7SUpsx4p9CEhdSCN/preview)
* [![Wikimedia Hackathon 2024 video](https://github.com/WolfgangFahl/snapquery/assets/1336221/460756cb-5379-4a93-b465-a5cb26f363bb)](https://youtu.be/-fHTdldf5Xo?t=2612)


### Model

![Class Diagram](http://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/WolfgangFahl/snapquery/main/snapquery.puml?fmt=svg&version=5)

## Authors

* [Wolfgang Fahl](http://www.bitplan.com/Wolfgang_Fahl)
* [Tim Holzheim](https://rwthcontacts.rwth-aachen.de/person/PER-46LT8TU)

# Features

## Planned

These are the planned features

* support for naming queries ([#9][i9]) ✅
* support for sharing queries (unique identifier) ([#2][i2]) ✅
* query multiple backends simultaneously and repeatedly
* stores queries and adaptations needed for different backends
* support user login
* support for spam protection
* support for rating queries
* support for commenting on queries
* support for detecting when a query returns different results between different backends
* support for query states: reliable, needs investigation, need verification
* support for autodetecting when a query returns fewer results than before (change in underlying data/model in
  Wikidata) -> needs investigation
* support for marking queries as reliable query by users
* support for seeing a state history per query
* support for storing query results so you don’t have to wait
* support for adding metadata to queries
    * add main subject (QID) to query
    * author -> id of author in the system
    * forked from x
* has REST API for data consumers e.g. LLM developers who want to present user-verified queries and data to users to
  increase reliability

## User stories

* as a user I want to know in advance if the query is returning what I expect
* as a user I want to [find all the rock bands starting with 'M'](http://snapquery.bitplan.com/query/wikidata.org/snapquery-examples/bands) in Wikidata without having to know how it is modeled
* as a user I want pay someone to help me get the information from Wikidata that I need
* as a user I want to know how a query performed in the past so I can trust that the underlying model is stable and I
  get the expected results
* as a user I want to comment on a query
* as a user I want to read comments from others on a query so I get and idea how reliable it is
* as a user I want to rate a query with 1-5 stars
* as a user I want to get information from multiple sparql engines at the same time
* as a user I don’t want to wait for a fresh query to finish and just get the information from the latest time a query
  succeeded.
* as a user I want a list of queries in the middleware
* as a user I want to sort the list based on the rate of queries
* as a user I want to annotate a query with a name
* as a user I want to annotate a query with a wikidata item as main subject
* as a user I want to see a list of queries that is tagged with a certain topic (wikidata item)
* as a user I want an API to get information from the middleware about queries
* as a user I want an api endpoint /list that gives me all queries with the main subject=Qxxxx
* as a user I want the system to warn me and annotate a query that no longer returns the data the user expects, ie. if a
  query suddenly start returning no results or fewer results
* as a user I want to see a state on a query
* as a user I want to log in using github to avoid the hassle of creating another account
* as a user I want to log in using gitlab to avoid the hassle of creating another account
* as a user I want to log in using facebook to avoid the hassle of creating another account
* as a user I want to know how many backends a query is working on, so I get an overview
* as a user I want to get query results immediately if possible so I don’t have to wait
* as a user I want to import a query by copy pasting a url from WDQS
* as a user I want to run a query on multiple backends with one click
* as a user I want to fork a query and build on it
* as a user I want an email if a query I'm watching needs investigation
* as a user I want settings to control whether I get email notifications or not for all queries I'm watching
* as a user I want to watch a query
* as a user I want to see the history of actions of other users
* as a user I want to know who created a query
* as a user I want a setting to get email about new comments on queries I'm watching
* as a user I want a setting to get emails about new queries every day, week, month
* as a user I want to star a query
* as a user I want to browse queries and sort by number of stars
* as a user I want to see who starred a query
* as a user I want to see a list of my notifications
* as a wikidata contributor I want to be able to override the “bad query” state
* as a wikidata user I want to be able to log in using my wmf credentials to avoid the hassle of creating another
  account
* as a wikidata user I want to link my current account to my wmf account so others can find me by username
* as a developer I want to expose the data in API endpoints
* as a LLM developer I want to consume the queries and use them to improve my LLM so it can suggest KNOWN GOOD queries
  to users

[i10]: https://github.com/WolfgangFahl/snapquery/issues/10
[i9]: https://github.com/WolfgangFahl/snapquery/issues/9

[i8]: https://github.com/WolfgangFahl/snapquery/issues/8

[i7]: https://github.com/WolfgangFahl/snapquery/issues/7

[i6]: https://github.com/WolfgangFahl/snapquery/issues/6

[i5]: https://github.com/WolfgangFahl/snapquery/issues/5

[i4]: https://github.com/WolfgangFahl/snapquery/issues/4

[i3]: https://github.com/WolfgangFahl/snapquery/issues/3

[i2]: https://github.com/WolfgangFahl/snapquery/issues/2

[i1]: https://github.com/WolfgangFahl/snapquery/issues/1