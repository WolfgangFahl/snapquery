# snapQuery
Tool that helps users preview, annotate, rate, comment, run and explore Wikidata queries on different sparql backends seamlessly. 
It enhances the user experience by storing the results and comparing the results from different backends and comparing over time. 

The purpose of the tool is to help users curate and collaborate on queries together and make sure they work as expected over time. 
Developers and data consumers can get access to the data via APIs.

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

## User stories
* as a user I want to know in advance if the query is returning what I expect
* as a user I want to find all the bands in Wikidata without having to know how it is modeled
* as a user I want pay someone to help me get the information from Wikidata that I need
* as a user I want to know how a query performed in the past so I can trust that the underlying model is stable and I get the expected results
* as a user I want to comment on a query
* as a user I want to read comments from others on a query so I get and idea how reliable it is
* as a user I want to rate a query with 1-5 stars
* as a user I want to get information from multiple sparql engines at the same time
* as a user I don’t want to wait for a fresh query to finish and just get the information from the latest time a query succeeded.
* as a user I want a list of queries in the middleware
* as a user I want to sort the list based on the rate of queries
* as a user I want to annotate a query with a name
* as a user I want to annotate a query with a wikidata item as main subject
* as a user I want to see a list of queries that is tagged with a certain topic (wikidata item)
* as a user I want an API to get information from the middleware about queries
* as a user I want an api endpoint /list that gives me all queries with the main subject=Qxxxx
* as a user I want the system to warn me and annotate a query that no longer returns the data the user expects, ie. if a query suddenly start returning no results or fewer results
* as a user I want to see a state on a query
* as a user I want to log in using github to avoid the hassle of creating another account
* as a user I want to log in using gitlab to avoid the hassle of creating another account
* as a user I want to log in using facebook to avoid the hassle of creating another account
* as a user I want to know how many backends a query is working on, so I get an overview
* as a user I want to get query results immediately if possible so I don’t have to wait
* as a user I want to import a query by copy pasting a url from WDQS
* as a user I want to run a query on multiple backends with one click
* as a user I want to fork a query and build on it
* as a wikidata contributor I want to be able to override the “bad query” state
* as a wikidata user I want to be able to log in using my wmf credentials to avoid the hassle of creating another account
* as a wikidata user I want to link my current account to my wmf account so others can find me by username
* as a developer I want to expose the data in API endpoints
* as a LLM developer I want to consume the queries and use them to improve my LLM so it can suggest KNOWN GOOD queries to users
